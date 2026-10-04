from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET
from .models import SiteSettings, Entry, ResumeSection, GalleryItem
from .rendering import rich_text


def asset_data(a):
    if not a or not a.public:
        return None
    return {
        "src": f"{settings.API_ORIGIN}/media/{a.pk}/?v={a.checksum}",
        "alt": a.alt,
        "width": a.width,
        "height": a.height,
        "mime": a.mime,
        "duration_ms": a.duration_ms,
    }


def live_entries():
    return (
        Entry.objects.filter(published=True, published_at__lte=timezone.now())
        .select_related("thumbnail")
        .prefetch_related("tags")
    )


def entry_data(e, detail=False):
    data = {
        "id": e.pk,
        "kind": e.kind,
        "category": e.category,
        "title": e.title,
        "slug": e.slug,
        "excerpt": e.excerpt,
        "published_at": e.published_at.isoformat(),
        "updated_at": e.updated_at.isoformat(),
        "thumbnail": asset_data(e.thumbnail),
        "tags": list(e.tags.values("name", "slug")),
        "seo_description": e.seo_description or e.excerpt[:180],
    }
    if detail:
        data.update(body_html=rich_text(e.body), repo_url=e.repo_url)
    return data


def json_response(data):
    r = JsonResponse(data)
    r["Cache-Control"] = "public, max-age=0, s-maxage=30"
    r["X-Robots-Tag"] = "noindex"
    return r


@require_GET
def site(request):
    s = get_object_or_404(SiteSettings, pk=1)
    return json_response(
        {
            "name": s.name,
            "title": s.title,
            "about_html": rich_text(s.about),
            "description": s.description,
            "email": s.email,
            "calendly": s.calendly,
            "linkedin": s.linkedin,
            "github": s.github,
            "social_image": asset_data(s.social_image),
            "privacy_html": rich_text(s.privacy),
        }
    )


@require_GET
def resume(request):
    result = []
    for section in ResumeSection.objects.filter(visible=True).prefetch_related("jobs__logo", "jobs__accomplishments"):
        jobs = []
        for j in section.jobs.all():
            if not j.visible:
                continue
            jobs.append(
                {
                    "title": j.title,
                    "company": j.company,
                    "start": j.start.strftime("%m/%Y"),
                    "end": j.end.strftime("%m/%Y") if j.end else "Present",
                    "logo": asset_data(j.logo),
                    "location": j.location,
                    "job_type": j.job_type,
                    "description_html": rich_text(j.description),
                    "accomplishments": [a.text for a in j.accomplishments.all()],
                }
            )
        result.append({"title": section.title, "body_html": rich_text(section.body), "jobs": jobs})
    return json_response({"sections": result})


@require_GET
def entries(request):
    qs = live_entries()
    kind = request.GET.get("kind", "")
    if kind in ["writing", "software", "blog"]:
        qs = qs.filter(kind=kind)
    category = request.GET.get("category", "")
    if category:
        qs = qs.filter(category=category[:16])
    q = request.GET.get("q", "").strip()[:200]
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(body__icontains=q))
    tag = request.GET.get("tag", "")[:80]
    if tag:
        qs = qs.filter(tags__slug=tag)
    page = Paginator(qs.distinct(), 24).get_page(request.GET.get("page", 1))
    return json_response(
        {
            "items": [entry_data(e) for e in page],
            "page": page.number,
            "pages": page.paginator.num_pages,
            "total": page.paginator.count,
        }
    )


@require_GET
def entry(request, slug):
    return json_response(entry_data(get_object_or_404(live_entries(), slug=slug), True))


@require_GET
def gallery(request, kind):
    if kind not in ["images", "videos"]:
        return JsonResponse({"error": "Invalid kind"}, status=404)
    items = GalleryItem.objects.filter(kind=kind, published=True).select_related("asset", "poster", "captions", "described_video")
    return json_response(
        {
            "items": [
                {
                    "id": g.pk,
                    "title": g.title,
                    "description_html": rich_text(g.description),
                    "asset": asset_data(g.asset),
                    "poster": asset_data(g.poster),
                    "captions": asset_data(g.captions),
                    "described_video": asset_data(g.described_video),
                    "transcript_html": rich_text(g.transcript),
                }
                for g in items
                if g.asset.public and (g.kind == "images" or (g.poster and g.poster.public))
            ]
        }
    )


@require_GET
def sitemap(request):
    return json_response(
        {
            "items": [
                {
                    "path": f"/{e.kind}/{e.slug}/",
                    "updated": e.updated_at.date().isoformat(),
                }
                for e in live_entries()
            ]
        }
    )


