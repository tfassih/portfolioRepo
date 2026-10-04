from django.conf import settings
from django.http import HttpResponse
from django.urls import path
from content.admin import studio
from content import api, media, exports, internal
urlpatterns = [
    path(settings.ADMIN_PATH, studio.urls),
    path("api/site/", api.site),
    path("api/resume/", api.resume),
    path("api/entries/", api.entries),
    path("api/entry/<slug:slug>/", api.entry),
    path("api/gallery/<str:kind>/", api.gallery),
    path("api/sitemap/", api.sitemap),
    path("media/<uuid:pk>/", media.media),
    path("resume.<str:fmt>", exports.download),
    path("internal/<str:action>/", internal.internal),
    path("jobs/daily/", internal.cron),
    path("health/", lambda request: HttpResponse("ok")),
    path(
        "robots.txt",
        lambda request: HttpResponse(
            "User-agent: *\nDisallow: /\n", content_type="text/plain"
        ),
    ),
]