import json
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlparse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from .models import Subscriber, Visit, RateBucket
from .guards import allow
from .emailing import send_confirmation, confirm, process_one


def response(data, status=200):
    r = JsonResponse(data, status=status)
    r["Cache-Control"] = "no-store"
    r["X-Robots-Tag"] = "noindex"
    return r


@csrf_exempt
@require_POST
def internal(request, action):
    supplied = request.headers.get("Authorization", "")
    if not secrets.compare_digest(supplied, "Bearer " + settings.INTERNAL_API_KEY):
        return response({"error": "Forbidden"}, 403)
    if len(request.body) > 4096:
        return response({"error": "Request too large"}, 413)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError()
        if action == "subscribe":
            email = str(data.get("email", "")).strip().lower()
            validate_email(email)
            if data.get("website"):
                return response({"ok": True})
            key = str(data.get("client_key", "unknown"))[:128]
            if not allow("subscribe-ip", key, 5, 3600):
                return response({"error": "Please try again later."}, 429)
            with transaction.atomic():
                s, created = Subscriber.objects.get_or_create(email=email)
                s = Subscriber.objects.select_for_update().get(pk=s.pk)
                if not created and s.requested_at > timezone.now() - timedelta(
                    minutes=15
                ):
                    return response({"ok": True})
                if not allow("confirmation-budget", "all", 80, 86400):
                    return response({"error": "Email is temporarily unavailable."}, 429)
                s.token, s.requested_at = uuid.uuid4(), timezone.now()
                s.save()
            send_confirmation(s)
            return response({"ok": True})
        if action == "confirm":
            confirm(uuid.UUID(str(data.get("token", ""))))
            return response({"ok": True})
        if action == "track":
            path = str(data.get("path", ""))[:240]
            allowed = [
                "/",
                "/resume/",
                "/art/",
                "/art/images/",
                "/art/videos/",
                "/writing/",
                "/software/",
                "/blog/",
                "/contact/",
                "/search/",
                "/privacy/",
            ]
            if path not in allowed:
                parts = path.strip("/").split("/")
                if len(parts) != 2 or parts[0] not in ["writing", "software", "blog"]:
                    return response({"error": "Invalid path"}, 400)
            if "?" in path or "#" in path:
                raise ValueError("Path only.")
            ref = urlparse(str(data.get("referrer", ""))).hostname or ""
            if not allow("track", str(data.get("client_key", "")), 120, 3600):
                return response({"ok": True})
            Visit.objects.get_or_create(
                event_id=uuid.UUID(str(data["event_id"])),
                defaults={"path": path, "referrer": ref[:180]},
            )
            return response({"ok": True})
    except (ValueError, ValidationError, KeyError):
        return response(
            {"error": "Check your input or request a new confirmation link."}, 400
        )
    except Exception:
        return response(
            {"error": "Service temporarily unavailable. Please retry later."}, 503
        )
    return response({"error": "Not found"}, 404)


@require_GET
def cron(request):
    if not settings.CRON_SECRET or not secrets.compare_digest(
        request.headers.get("Authorization", ""), "Bearer " + settings.CRON_SECRET
    ):
        return response({"error": "Forbidden"}, 403)
    RateBucket.objects.filter(expires_at__lt=timezone.now()).delete()
    Visit.objects.filter(created_at__lt=timezone.now() - timedelta(days=90)).delete()
    Subscriber.objects.filter(
        confirmed_at__isnull=True, requested_at__lt=timezone.now() - timedelta(days=7)
    ).delete()
    return response({"result": process_one()})