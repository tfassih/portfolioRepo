from datetime import timedelta
from html import escape
from urllib.parse import quote
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Notification, Subscriber


def resend(method, path, data=None, key=None):
    if not settings.RESEND_API_KEY:
        raise ValueError("Configure Resend before enabling email.")
    headers = {"Authorization": "Bearer " + settings.RESEND_API_KEY}
    if key:
        headers["Idempotency-Key"] = key
    r = requests.request(
        method,
        "https://api.resend.com" + path,
        json=data,
        headers=headers,
        timeout=(5, 15),
    )
    r.raise_for_status()
    return r.json() if r.content else {}


def send_confirmation(subscriber):
    url = f"{settings.SITE_ORIGIN}/subscribe/confirm/?token={subscriber.token}"
    return resend(
        "POST",
        "/emails",
        {
            "from": settings.EMAIL_FROM,
            "to": [subscriber.email],
            "subject": "Confirm your subscription to Thomas Fassih",
            "html": "<p>You requested blog notifications.</p>"
            f'<p><a href="{escape(url)}">Confirm your subscription</a></p>'
            "<p>If you did not request this, ignore this email.</p>",
            "text": f"Confirm your subscription: {url}\nIgnore this if you did not request it.",
        },
        key=f"confirm/{subscriber.token}",
    )


def confirm(token):
    with transaction.atomic():
        s = Subscriber.objects.select_for_update().filter(token=token).first()
        if not s or s.requested_at < timezone.now() - timedelta(hours=48):
            raise ValueError("Confirmation link expired. Subscribe again.")
        # Reconcile by email after any earlier partial provider operation.
        # Only this explicit confirmation may opt someone back in.
        try:
            result = resend("GET", "/contacts/" + quote(s.email, safe=""))
        except requests.HTTPError as error:
            if error.response.status_code != 404:
                raise
            result = resend(
                "POST", "/contacts", {"email": s.email, "unsubscribed": False}
            )
        s.contact_id = result["id"]
        resend("PATCH", f"/contacts/{s.contact_id}", {"unsubscribed": False})
        s.save(update_fields=["contact_id"])
        resend(
            "POST", f"/contacts/{s.contact_id}/segments/{settings.RESEND_SEGMENT_ID}"
        )
        s.confirmed_at = timezone.now()
        s.token = None
        s.save(update_fields=["confirmed_at", "token"])


def process_one(pk=None):
    # Commit a claim BEFORE any external operation. A crashed claim is
    # deliberately excluded from automatic retries; inspect it manually.
    with transaction.atomic():
        qs = (
            Notification.objects.select_for_update(skip_locked=True)
            .filter(
                status__in=["queued", "draft"],
                entry__published=True,
                entry__published_at__lte=timezone.now(),
            )
            .select_related("entry")
        )
        if pk:
            qs = qs.filter(pk=pk)
        job = qs.order_by("pk").first()
        if not job:
            return "Nothing queued."
        if not settings.EMAIL_POSTAL_ADDRESS:
            return "Set EMAIL_POSTAL_ADDRESS before sending notifications."
        job.status = "preparing"
        job.save(update_fields=["status", "updated_at"])
    entry = job.entry
    url = f"{settings.SITE_ORIGIN}/blog/{entry.slug}/"
    try:
        if not job.broadcast_id:
            draft = resend(
                "POST",
                "/broadcasts",
                {
                    "segment_id": settings.RESEND_SEGMENT_ID,
                    "from": settings.EMAIL_FROM,
                    "name": f"blog-{entry.pk}",
                    "subject": entry.title,
                    "html": f"<h1>{escape(entry.title)}</h1>"
                    f"<p>{escape(entry.excerpt)}</p>"
                    f'<p><a href="{escape(url)}">Read the post</a></p>'
                    '<p><a href="{{{RESEND_UNSUBSCRIBE_URL}}}">Unsubscribe</a></p>'
                    f"<p>{escape(settings.EMAIL_POSTAL_ADDRESS)}</p>",
                },
            )
            job.broadcast_id = draft["id"]
        job.status = "sending"
        job.save()  # Durable broadcast ID and state before the send call.
        resend("POST", f"/broadcasts/{job.broadcast_id}/send", {})
        job.status, job.error = "sent", ""
    except Exception as error:
        job.status = "review"
        job.error = type(error).__name__ + ": inspect the Resend dashboard."
    job.save()
    return f"Notification {job.pk}: {job.status}"