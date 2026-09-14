"""
Dashboard screenshot service.
Runs Playwright in an isolated subprocess to avoid event loop conflicts
with the main project's WindowsSelectorEventLoopPolicy.
"""

import subprocess
import sys
from pathlib import Path

from app.core.logging import log_process, log_success, log_error


SCREENSHOTS_DIR = Path("reports/screenshots")


def _ensure_screenshots_dir() -> Path:
    """Ensure the screenshots output directory exists."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS_DIR


def _build_capture_script(
    url: str,
    output_path: Path,
    width: int,
    height: int,
) -> str:
    """Build a standalone Python script that captures the screenshot."""
    return (
        "import asyncio\n"
        "from playwright.async_api import async_playwright\n"
        "async def main():\n"
        "    async with async_playwright() as pw:\n"
        "        browser = await pw.chromium.launch(headless=True)\n"
        f"        context = await browser.new_context("
        f"viewport={{'width': {width}, 'height': {height}}}, "
        f"device_scale_factor=2)\n"
        "        page = await context.new_page()\n"
        f"        await page.goto({url!r}, wait_until='networkidle', timeout=60000)\n"
        "        await page.wait_for_timeout(3000)\n"
        f"        await page.screenshot(path={str(output_path)!r}, full_page=True)\n"
        "        await browser.close()\n"
        "asyncio.run(main())\n"
    )


def _capture_in_subprocess(
    url: str,
    output_path: Path,
    width: int,
    height: int,
) -> None:
    """Run a standalone Playwright script as a subprocess."""
    script = _build_capture_script(url, output_path, width, height)

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(f"Playwright subprocess failed: {stderr[:400]}")


async def capture_dashboard_screenshot(
    dashboard_url: str,
    output_filename: str,
    width: int = 1400,
    height: int = 900,
) -> str | None:
    """
    Capture a screenshot of a public dashboard URL.

    Runs Playwright in a separate Python process to fully isolate the
    event loop from the main application.

    Args:
        dashboard_url: Public Metabase dashboard URL.
        output_filename: Target filename (e.g. 'fraud_dashboard.png').
        width: Viewport width in pixels.
        height: Viewport height in pixels.

    Returns:
        Absolute path to the saved PNG, or None on failure.
    """
    if not dashboard_url or not dashboard_url.strip():
        log_error("screenshot: empty URL")
        return None

    _ensure_screenshots_dir()
    output_path = SCREENSHOTS_DIR / output_filename

    log_process(f"screenshot: capturing {dashboard_url}")

    try:
        _capture_in_subprocess(dashboard_url, output_path, width, height)
    except FileNotFoundError:
        log_error("screenshot: python executable not found")
        return None
    except subprocess.TimeoutExpired:
        log_error("screenshot: subprocess timed out")
        return None
    except Exception as exc:
        log_error(f"screenshot: failed: {exc}")
        return None

    if not output_path.exists():
        log_error("screenshot: file not created")
        return None

    log_success(f"screenshot: saved to {output_path}")
    return str(output_path.resolve())