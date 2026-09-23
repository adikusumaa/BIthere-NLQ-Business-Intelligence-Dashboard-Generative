"""
In-memory progress tracker for long-running jobs.
One job per key (workspace_id:job_name). Resets each time a new job starts.
"""

import time
from typing import Any, Dict, Optional


_jobs: Dict[str, Dict[str, Any]] = {}


def start_job(key: str, label: str = "") -> None:
    _jobs[key] = {
        "status": "running",
        "label": label,
        "current": 0,
        "total": 0,
        "percent": 0,
        "message": "",
        "started_at": time.time(),
    }


def update_job(
    key: str,
    current: Optional[int] = None,
    total: Optional[int] = None,
    message: Optional[str] = None,
) -> None:
    job = _jobs.get(key)
    if not job:
        return
    if current is not None:
        job["current"] = current
    if total is not None:
        job["total"] = total
    if message is not None:
        job["message"] = message
    c = job["current"]
    t = job["total"]
    if t > 0:
        job["percent"] = min(99, int(c * 100 / t))


def finish_job(key: str, result: Optional[Dict[str, Any]] = None) -> None:
    job = _jobs.get(key)
    if not job:
        return
    job["status"] = "done"
    job["percent"] = 100
    job["result"] = result or {}
    job["finished_at"] = time.time()


def fail_job(key: str, error: str) -> None:
    job = _jobs.get(key)
    if not job:
        return
    job["status"] = "error"
    job["error"] = error
    job["finished_at"] = time.time()


def get_job(key: str) -> Optional[Dict[str, Any]]:
    return _jobs.get(key)