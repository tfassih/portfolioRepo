from copy import deepcopy
import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from content.models import SiteSettings
from content.themes import default_theme_config, validate_theme_config


class ThemeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = SiteSettings.objects.create(name="Existing owner")
        cls.user = get_user_model().objects.create_superuser("editor", "editor@example.test", "test-password")

    def test_defaults_and_api_preload_every_theme(self):
        validate_theme_config(self.site.theme_config)
        response = self.client.get("/api/site/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["theme_config"], default_theme_config())
        self.assertEqual(response.json()["name"], "Existing owner")
        self.assertEqual(len(response.json()["theme_config"]["themes"]), 3)

    def test_default_documents_are_independent(self):
        a, b = default_theme_config(), default_theme_config()
        a["themes"][0]["name"] = "Changed"
        self.assertEqual(b["themes"][0]["name"], "Marginalia")

    def test_invalid_structure_ids_defaults_and_colors_are_rejected(self):
        good = default_theme_config()
        cases = [None, [], {}, {**good, "version": True}, {**good, "themes": []},
                 {**good, "themes": good["themes"] * 8}, {**good, "default": "missing"},
                 {**good, "default": []}, {**good, "extra": 1}]
        for update in [
            {"id": "</style><script>"}, {"id": []}, {"id": "a" * 33},
            {"name": ""}, {"name": "n" * 51}, {"light": {}},
            {"dark": {**good["themes"][0]["dark"], "accent": "url(https://example.test)"}},
            {"light": {**good["themes"][0]["light"], "paper": "#fff; color:red"}},
        ]:
            data = deepcopy(good)
            data["themes"][0].update(update)
            cases.append(data)
        duplicate = deepcopy(good)
        duplicate["themes"][1]["id"] = "marginalia"
        cases.append(duplicate)
        for config in cases:
            with self.subTest(config=config):
                with self.assertRaises(ValidationError):
                    validate_theme_config(config)

    def test_invalid_stored_data_falls_back_without_breaking_the_site(self):
        SiteSettings.objects.filter(pk=1).update(theme_config={"invalid": True})
        with self.assertLogs("content.themes", level="WARNING"):
            response = self.client.get("/api/site/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["theme_config"], default_theme_config())

    def payload(self, config=None):
        return {"name": "Existing owner", "title": "Polymath",
                "theme_config": json.dumps(config or default_theme_config()), "_save": "Save"}

    def test_admin_edits_and_exports_database_configuration(self):
        self.client.force_login(self.user)
        config = default_theme_config()
        config["default"] = "ocean"
        url = "/studio-admin/content/sitesettings/1/"
        response = self.client.post(url + "change/", self.payload(config))
        self.assertEqual(response.status_code, 302)
        self.site.refresh_from_db()
        self.assertEqual(self.site.theme_config, config)
        exported = self.client.get(url + "themes.json")
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(exported.json(), config)
        self.assertIn("attachment", exported["Content-Disposition"])
        self.assertEqual(self.client.post(url + "themes.json").status_code, 405)
        self.assertEqual(self.client.get("/api/site/").json()["theme_config"]["default"], "ocean")

    def test_admin_import_accepts_utf8_bom_and_replaces_configuration(self):
        self.client.force_login(self.user)
        config = default_theme_config()
        config["default"] = "forest"
        data = self.payload()
        data["theme_file"] = SimpleUploadedFile("themes.json", json.dumps(config).encode("utf-8-sig"), "application/json")
        response = self.client.post("/studio-admin/content/sitesettings/1/change/", data)
        self.assertEqual(response.status_code, 302)
        self.site.refresh_from_db()
        self.assertEqual(self.site.theme_config, config)

    def test_invalid_import_or_editor_content_leaves_saved_settings_intact(self):
        self.client.force_login(self.user)
        url = "/studio-admin/content/sitesettings/1/change/"
        for filename, content in [("themes.json", b"not json"), ("themes.txt", b"{}"),
                                  ("themes.json", b"x" * (65536 + 1)), ("themes.json", b"[]")]:
            with self.subTest(filename=filename, size=len(content)):
                data = self.payload()
                data["theme_file"] = SimpleUploadedFile(filename, content)
                self.assertEqual(self.client.post(url, data).status_code, 200)
                self.site.refresh_from_db()
                self.assertEqual(self.site.theme_config, default_theme_config())
        bad = default_theme_config()
        bad["default"] = "missing"
        self.assertContains(self.client.post(url, self.payload(bad)), "Default must match")
        self.site.refresh_from_db()
        self.assertEqual(self.site.theme_config, default_theme_config())

    def test_theme_admin_requires_authorization(self):
        url = "/studio-admin/content/sitesettings/1/themes.json"
        self.assertEqual(self.client.get(url).status_code, 302)
        viewer = get_user_model().objects.create_user("staff", is_staff=True)
        self.client.force_login(viewer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post("/studio-admin/content/sitesettings/1/change/", self.payload()).status_code, 403)

    def test_bundled_text_colors_have_readable_contrast(self):
        def luminance(color):
            channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
            return sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722)))
        for theme in default_theme_config()["themes"]:
            for mode in ["light", "dark"]:
                for text in ["ink", "muted", "accent"]:
                    for surface in ["paper", "panel"]:
                        with self.subTest(theme=theme["id"], mode=mode, text=text, surface=surface):
                            a, b = sorted([luminance(theme[mode][text]), luminance(theme[mode][surface])])
                            self.assertGreaterEqual((b + 0.05) / (a + 0.05), 4.5)


class ThemeMigrationTests(TransactionTestCase):
    def test_existing_settings_and_gallery_survive_upgrade(self):
        previous = [("content", "0002_alter_galleryitem_kind")]
        current = [("content", "0003_sitesettings_theme_config")]
        executor = MigrationExecutor(connection)
        try:
            executor.migrate(previous)
            old = executor.loader.project_state(previous).apps
            old.get_model("content", "SiteSettings").objects.create(pk=1, name="Preserved owner", about="Existing text")
            asset = old.get_model("content", "Asset").objects.create(name="Photo", drive_id="migration-photo", public=True)
            old.get_model("content", "GalleryItem").objects.create(kind="photography", title="Preserved photo", asset=asset)
            executor = MigrationExecutor(connection)
            executor.migrate(current)
            new = executor.loader.project_state(current).apps
            site = new.get_model("content", "SiteSettings").objects.get(pk=1)
            self.assertEqual(site.name, "Preserved owner")
            self.assertEqual(site.about, "Existing text")
            self.assertEqual(site.theme_config, default_theme_config())
            self.assertEqual(new.get_model("content", "GalleryItem").objects.get().title, "Preserved photo")
        finally:
            MigrationExecutor(connection).migrate(current)
