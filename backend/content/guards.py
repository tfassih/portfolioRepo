import hashlib
import hmac
import time
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from .models import RateBucket


def allow(scope, identity, limit, seconds):
    bucket = int(time.time()) // seconds
    raw = f"{scope}:{identity}:{bucket}".encode()
    key = hmac.new(settings.SECRET_KEY.encode(), raw, hashlib.sha256).hexdigest()
    with transaction.atomic():
        item, _ = RateBucket.objects.get_or_create(
            key=key,
            defaults={"expires_at": timezone.now() + timedelta(seconds=seconds * 2)},
        )
        item = RateBucket.objects.select_for_update().get(pk=item.pk)
        if item.count >= limit:
            return False
        item.count += 1
        item.save(update_fields=["count"])
    return True


class AdminLoginThrottle:
    def __init__(self, get_response):
        self.get_response = get_response

        
    def __call__(self, request):
        if (
            request.method == "POST"
            and request.path == "/" + settings.ADMIN_PATH + "login/"
        ):
            # Trust this header only behind Vercel, which sets it.
            ip = request.META.get(
                "HTTP_X_VERCEL_FORWARDED_FOR",
                request.META.get("REMOTE_ADDR", "unknown"),
            )
            if not allow("admin-login", ip, 20, 3600):
                return HttpResponse("Too many attempts. Try again later.", status=429)
        return self.get_response(request)