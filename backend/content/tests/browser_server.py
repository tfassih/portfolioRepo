"""Disposable Django backend for browser tests, with local media fixtures."""
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.test_settings"

import django
from django.conf import settings
from django.core.management import call_command
from django.http import FileResponse, HttpResponse
from django.urls import path


with TemporaryDirectory(prefix="portfolio-browser-tests-") as directory:
    settings.DATABASES["default"]["NAME"] = str(Path(directory) / "tests.sqlite3")
    django.setup()
    call_command("migrate", verbosity=0)

    from content.models import Asset, Entry, GalleryItem, SiteSettings
    from config import urls

    SiteSettings.objects.create(description="Test portfolio", about="A portfolio of art and software.")
    image = Asset.objects.create(name="Still", drive_id="test-still", mime="image/svg+xml", alt="Test landscape", public=True)
    clip = Asset.objects.create(name="Clip", drive_id="test-clip", mime="video/mp4", public=True)
    for kind, title, position in [
        ("images", "Studio render", 0),
        ("photography", "River light", 0),
        ("photography", "Evening street", 1),
    ]:
        GalleryItem.objects.create(kind=kind, title=title, position=position, asset=image, published=True, description="A **portfolio** image.")
    GalleryItem.objects.create(kind="videos", title="Motion study", asset=clip, poster=image, published=True)
    Entry.objects.create(kind="software", title="Example project", slug="example-project", body="Project details", published=True)

    def media_fixture(request, pk):
        if pk == clip.pk:
            response = FileResponse((Path(__file__).parent / "fixtures" / "clip.mp4").open("rb"), content_type="video/mp4")
        else:
            response = HttpResponse('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400"><rect width="640" height="400" fill="#695b4d"/></svg>', content_type="image/svg+xml")
        response["Access-Control-Allow-Origin"] = settings.SITE_ORIGIN
        return response

    urls.urlpatterns.insert(0, path("media/<uuid:pk>/", media_fixture))
    call_command("runserver", "127.0.0.1:8001", use_reloader=False, verbosity=0)
