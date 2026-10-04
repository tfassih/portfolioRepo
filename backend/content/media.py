from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from requests import RequestException
from .models import Asset
from .drive import byte_range, read_bytes, SMALL_LIMIT


@require_http_methods(["GET", "HEAD", "OPTIONS"])
def media(request, pk):
    a = get_object_or_404(Asset, pk=pk, public=True)
    if request.method == "OPTIONS":
        response = HttpResponse(status=204)
    else:
        requested = request.headers.get("Range")
        is_video = a.mime.startswith("video/")
        try:
            if requested:
                start, end = byte_range(requested, a.size)
            else:
                start, end = 0, a.size - 1
                if a.size > SMALL_LIMIT and request.method != "HEAD":
                    raise ValueError("Large media requires a byte-range request.")
        except ValueError:
            response = HttpResponse(status=416 if requested else 400)
            response["Content-Range"] = f"bytes */{a.size}"
        else:
            partial = bool(requested)
            try:
                body = b"" if request.method == "HEAD" else read_bytes(a, start, end)
            except (ValueError, RequestException):
                response = HttpResponse("Media temporarily unavailable.", status=503)
                response["Cache-Control"] = "no-store"
            else:
                response = HttpResponse(
                    body, content_type=a.mime, status=206 if partial else 200
                )
                response["Content-Length"] = str(end - start + 1)
                if partial:
                    response["Content-Range"] = f"bytes {start}-{end}/{a.size}"
                response["Cache-Control"] = (
                    "no-store" if is_video else "public, max-age=300, s-maxage=300"
                )
    response["Accept-Ranges"] = "bytes"
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Range"
    response["Access-Control-Expose-Headers"] = "Content-Range, Accept-Ranges"
    response["X-Content-Type-Options"] = "nosniff"
    return response