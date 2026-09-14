"""
Supabase Storage helper for report screenshots.
"""

from pathlib import Path

from app.core.security import get_supabase_client
from app.core.logging import log_process, log_success, log_error


BUCKET = "bithere-reports"


def upload_screenshot(local_path: str, remote_name: str) -> str | None:
    """
    Upload a PNG to Supabase Storage and return its public URL.
    """
    try:
        path = Path(local_path)
        if not path.exists():
            log_error(f"storage: file not found {local_path}")
            return None

        supabase = get_supabase_client()
        with open(path, "rb") as fh:
            data = fh.read()

        supabase.storage.from_(BUCKET).upload(
            path=remote_name,
            file=data,
            file_options={"content-type": "image/png", "upsert": "true"},
        )

        public = supabase.storage.from_(BUCKET).get_public_url(remote_name)
        log_success(f"storage: uploaded {remote_name}")
        return public
    except Exception as exc:
        log_error(f"storage: upload failed: {exc}")
        return None