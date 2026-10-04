import json
import re
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from django.conf import settings


SMALL_LIMIT = 2 * 1024 * 1024
CHUNK_LIMIT = 2 * 1024 * 1024
MIMES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/avif",
    "video/mp4",
    "video/webm",
    "text/vtt",
    }


def session():
    info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
    credentials = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return AuthorizedSession(credentials)


def metadata(file_id):
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,180}", file_id):
        raise ValueError("Paste a Drive file ID, not its sharing URL.")
    with session() as client:
        r = client.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={
                "fields": "id,name,mimeType,size,parents,md5Checksum,"
                "imageMediaMetadata,videoMediaMetadata,trashed",
                "supportsAllDrives": "true",
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
    # Use one flat publishing folder. Originals may live elsewhere.
    if settings.GOOGLE_DRIVE_FOLDER_ID not in data.get("parents", []):
        raise ValueError("File must be directly inside the publishing folder.")
    if data.get("trashed") or data.get("mimeType") not in MIMES:
        raise ValueError("Use a supported binary image, video, or WebVTT file.")
    size = int(data.get("size", 0))
    if size <= 0:
        raise ValueError("File is empty or unavailable.")
    if not data["mimeType"].startswith("video/") and size > SMALL_LIMIT:
        raise ValueError("Images and captions must be 2 MiB or smaller.")
    return data


def import_metadata(asset):
    data = metadata(asset.drive_id)
    media = data.get("imageMediaMetadata", data.get("videoMediaMetadata", {}))
    asset.mime = data["mimeType"]
    asset.size = int(data["size"])
    asset.width = int(media.get("width", 0))
    asset.height = int(media.get("height", 0))
    asset.duration_ms = int(media.get("durationMillis", 0))
    asset.checksum = data.get("md5Checksum", "")
    if not asset.name:
        asset.name = data["name"]


def byte_range(header, size):
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", header or "")
    if not match or not any(match.groups()):
        raise ValueError("Use one byte range.")
    first, last = match.groups()
    if first:
        start = int(first)
        end = min(int(last), size - 1) if last else size - 1
    else:
        suffix = int(last)
        if suffix <= 0:
            raise ValueError("Empty suffix.")
        start, end = max(0, size - suffix), size - 1
    if start >= size or start > end:
        raise ValueError("Range outside file.")
    return start, min(end, start + CHUNK_LIMIT - 1)


def read_bytes(asset, start, end):
    expected = end - start + 1
    with session() as client:
        with client.get(
            f"https://www.googleapis.com/drive/v3/files/{asset.drive_id}",
            params={"alt": "media", "supportsAllDrives": "true"},
            headers={"Range": f"bytes={start}-{end}"},
            stream=True,
            timeout=(5, 20),
        ) as r:
            r.raise_for_status()
            if r.status_code != 206:
                raise ValueError("Drive did not honor the byte range.")
            if r.headers.get("Content-Range") != f"bytes {start}-{end}/{asset.size}":
                raise ValueError("Asset changed. Re-import its metadata.")
            data = bytearray()
            for chunk in r.iter_content(64 * 1024):
                data.extend(chunk)
                if len(data) > expected:
                    raise ValueError("Upstream response exceeds its declared range.")
    if len(data) != expected:
        raise ValueError("Incomplete media response.")
    return bytes(data)