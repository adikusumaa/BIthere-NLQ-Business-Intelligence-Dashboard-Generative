"""
File upload handler for workspace datasets.
Validates extension and size; stores under UPLOAD_DIR/{workspace_id}/.
"""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.logging import logger


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet"}


class UploadError(Exception):
    """Raised when upload validation or storage fails."""


def _workspace_dir(workspace_id: str) -> str:
    path = os.path.join(settings.UPLOAD_DIR, workspace_id)
    os.makedirs(path, exist_ok=True)
    return path


def _validate_filename(filename: str) -> str:
    if not filename:
        raise UploadError("Filename is required")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError(
            f"Extension '{ext}' not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )
    return ext


async def save_upload(workspace_id: str, file: UploadFile) -> dict:
    """Save uploaded file to disk and return metadata."""
    if not file or not file.filename:
        raise UploadError("No file provided")

    ext = _validate_filename(file.filename)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(_workspace_dir(workspace_id), stored_name)

    total = 0
    try:
        with open(stored_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    out.close()
                    os.remove(stored_path)
                    raise UploadError(
                        f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit"
                    )
                out.write(chunk)
    except UploadError:
        raise
    except Exception as exc:
        if os.path.exists(stored_path):
            os.remove(stored_path)
        raise UploadError(f"Failed to save file: {exc}") from exc

    logger.info(f"[SUCCESS] File saved: {stored_path} ({total} bytes)")

    return {
        "workspace_id": workspace_id,
        "original_filename": file.filename,
        "stored_path": stored_path,
        "stored_filename": stored_name,
        "extension": ext,
        "size_bytes": total,
    }


def delete_upload(stored_path: str) -> bool:
    """Remove a stored upload file."""
    if os.path.exists(stored_path):
        os.remove(stored_path)
        logger.info(f"[SUCCESS] File deleted: {stored_path}")
        return True
    return False