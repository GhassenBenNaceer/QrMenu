"""
File storage service.

Supports three backends controlled by STORAGE_PROVIDER env var:
  - "local"  → saves to backend/static/uploads/ and serves via FastAPI StaticFiles
  - "s3"     → AWS S3 via boto3
  - "r2"     → Cloudflare R2 (S3-compatible, zero egress fees)
"""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

STATIC_UPLOAD_DIR = Path(__file__).parent.parent.parent / "static" / "uploads"


async def upload_file(file: UploadFile, folder: str) -> str:
    """Upload a file and return its public CDN URL."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images are allowed")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5 MB")

    ext = _get_extension(file.content_type)
    filename = f"{uuid.uuid4()}{ext}"

    if settings.STORAGE_PROVIDER == "local":
        return await _save_local(contents, folder, filename)
    elif settings.STORAGE_PROVIDER in ("s3", "r2"):
        return await _save_s3(contents, folder, filename, file.content_type)
    else:
        raise ValueError(f"Unknown storage provider: {settings.STORAGE_PROVIDER}")


async def _save_local(contents: bytes, folder: str, filename: str) -> str:
    dest = STATIC_UPLOAD_DIR / folder
    dest.mkdir(parents=True, exist_ok=True)
    (dest / filename).write_bytes(contents)
    return f"{settings.CDN_BASE_URL}/uploads/{folder}/{filename}"


async def _save_s3(contents: bytes, folder: str, filename: str, content_type: str) -> str:
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        raise RuntimeError("boto3 is required for S3/R2 storage. Run: pip install boto3")

    key = f"{folder}/{filename}"
    kwargs = dict(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

    s3 = boto3.client("s3", **kwargs)
    try:
        s3.put_object(
            Bucket=settings.STORAGE_BUCKET,
            Key=key,
            Body=contents,
            ContentType=content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {e}")

    return f"{settings.CDN_BASE_URL}/{key}"


def _get_extension(content_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(content_type, ".jpg")
