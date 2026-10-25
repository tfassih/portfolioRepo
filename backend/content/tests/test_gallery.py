from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest import skipUnless
import uuid

from content.models import Asset, GalleryItem, SiteSettings, Visit


class GalleryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.image = Asset.objects.create(name="Photo", drive_id="photo", public=True, mime="image/jpeg")
        cls.video = Asset.objects.create(name="Clip", drive_id="video", public=True, mime="video/mp4")
        cls.private = Asset.objects.create(name="Private", drive_id="private", mime="image/jpeg")
        cls.user = get_user_model().objects.create_superuser("editor", "editor@example.test", "test-password")

    def test_photography_has_its_own_ordered_public_feed(self):
        for title, kind, asset, published, position in [
            ("Second", "photography", self.image, True, 2),
            ("First", "photography", self.image, True, 1),
            ("Draft", "photography", self.image, False, 0),
            ("Private", "photography", self.private, True, 0),
            ("Render", "images", self.image, True, 0),
        ]:
            GalleryItem.objects.create(title=title, kind=kind, asset=asset, published=published, position=position)
        response = self.client.get("/api/gallery/photography/")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual([item["title"] for item in items], ["First", "Second"])
        self.assertTrue(items[0]["asset"]["src"].startswith("http://127.0.0.1:8001/media/"))
        self.assertIsNone(items[0]["poster"])
        self.assertEqual(self.client.get("/api/gallery/images/").json()["items"][0]["title"], "Render")

    def test_photography_validation(self):
        photo = GalleryItem(kind="photography", title="Photo", asset=self.image, published=True)
        photo.full_clean()  # No video poster is required.
        photo.asset = self.video
        with self.assertRaisesMessage(ValidationError, "image/"):
            photo.full_clean()
        photo.asset = self.private
        with self.assertRaisesMessage(ValidationError, "must be public"):
            photo.full_clean()

    def test_existing_video_validation_and_feed(self):
        clip = GalleryItem(kind="videos", title="Clip", asset=self.video, published=True)
        with self.assertRaisesMessage(ValidationError, "Poster is required"):
            clip.full_clean()
        clip.poster = self.image
        clip.full_clean()
        clip.save()
        data = self.client.get("/api/gallery/videos/").json()["items"]
        self.assertEqual([item["title"] for item in data], ["Clip"])
        self.assertEqual(data[0]["asset"]["mime"], "video/mp4")
        self.image.public = False
        self.image.save()
        self.assertEqual(self.client.get("/api/gallery/videos/").json()["items"], [])

    def test_empty_unknown_and_non_get(self):
        self.assertEqual(self.client.get("/api/gallery/photography/").json(), {"items": []})
        self.assertEqual(self.client.get("/api/gallery/unknown/").status_code, 404)
        self.assertEqual(self.client.post("/api/gallery/images/").status_code, 405)

    def test_admin_can_create_and_filter_photography(self):
        self.client.force_login(self.user)
        url = "/studio-admin/content/galleryitem/"
        response = self.client.post(url + "add/", {
            "kind": "photography", "title": "Admin photo", "asset": str(self.image.pk),
            "position": 0, "published": "on", "_save": "Save",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(GalleryItem.objects.filter(kind="photography", title="Admin photo").exists())
        self.assertContains(self.client.get(url + "?kind__exact=photography"), "Admin photo")
        self.assertContains(self.client.get(url + "add/"), 'value="photography"')

    def test_photography_visits_are_recorded(self):
        response = self.client.post("/internal/track/", {
            "event_id": str(uuid.uuid4()), "path": "/art/photography/", "referrer": "",
        }, content_type="application/json", HTTP_AUTHORIZATION="Bearer " + settings.INTERNAL_API_KEY)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Visit.objects.filter(path="/art/photography/").exists())

    def test_existing_public_endpoints(self):
        SiteSettings.objects.create()
        for url in ["/health/", "/api/site/", "/api/resume/", "/api/entries/", "/api/sitemap/", "/resume.docx"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    @skipUnless(
        all((settings.BASE_DIR / "fonts" / name).exists() for name in ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf"]),
        "Existing PDF export requires untracked backend/fonts/DejaVuSans*.ttf files.",
    )
    def test_pdf_export(self):
        SiteSettings.objects.create()
        response = self.client.get("/resume.pdf")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
