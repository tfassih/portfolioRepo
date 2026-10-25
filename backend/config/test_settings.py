"""Isolated settings for tests; never connect to configured external services."""
import os

os.environ.update({
    "DEBUG": "1",
    "DJANGO_SECRET_KEY": "test-only-not-for-deployment",
    "INTERNAL_API_KEY": "test-only-internal-key",
    "DATABASE_URL": "sqlite:///:memory:",
    "ALLOWED_HOSTS": "localhost,127.0.0.1,testserver",
    "SITE_ORIGIN": "http://127.0.0.1:4322",
    "API_ORIGIN": "http://127.0.0.1:8001",
    "ADMIN_PATH": "studio-admin",
    "GOOGLE_DRIVE_FOLDER_ID": "",
    "GOOGLE_SERVICE_ACCOUNT_JSON": "",
    "RESEND_API_KEY": "",
    "RESEND_SEGMENT_ID": "",
    "CRON_SECRET": "",
})

from .settings import *  # noqa: F403,E402

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
