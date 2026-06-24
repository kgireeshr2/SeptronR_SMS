import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from app.core.config import settings


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


async def save_upload_file(
    upload_file: UploadFile,
    folder: str = "misc",
    allowed_types: set | None = None,
) -> str:
    """
    Save an uploaded file to local storage (dev) or S3 (prod).

    Returns the relative path or S3 key of the saved file.
    """
    if allowed_types is None:
        allowed_types = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES

    # Validate content type
    if upload_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{upload_file.content_type}' is not allowed.",
        )

    # Validate file size
    content = await upload_file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the {settings.MAX_FILE_SIZE_MB}MB limit.",
        )

    ext = os.path.splitext(upload_file.filename or "file")[1]
    filename = f"{uuid.uuid4().hex}{ext}"

    if settings.STORAGE_BACKEND == "s3":
        return await _upload_to_s3(content, folder, filename, upload_file.content_type)

    return await _save_locally(content, folder, filename)


async def _save_locally(content: bytes, folder: str, filename: str) -> str:
    """Save file to local filesystem."""
    upload_path = os.path.join(settings.UPLOAD_DIR, folder)
    os.makedirs(upload_path, exist_ok=True)
    file_path = os.path.join(upload_path, filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    return f"{folder}/{filename}"


async def _upload_to_s3(
    content: bytes, folder: str, filename: str, content_type: str
) -> str:
    """Upload file to AWS S3."""
    import boto3
    from botocore.exceptions import ClientError

    s3_key = f"{folder}/{filename}"
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=content,
            ContentType=content_type,
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")
    return s3_key


def get_file_url(path: str) -> str:
    """Convert stored path/key to accessible URL."""
    if settings.STORAGE_BACKEND == "s3":
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{path}"
    return f"/uploads/{path}"
