"""
Dashboard screenshot service.
Captures all tabs of a public Metabase dashboard via Playwright subprocess.
"""

import subprocess
import sys
from pathlib import Path

from app.core.logging import log_process, log_success, log_error


SCREENSHOTS_DIR = Path("reports/screenshots")


def _ensure_dir() -> Path:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS_DIR


def _build_capture_script(url: str, output_dir: Path, width: int, height: int) -> str:
    """Build a standalone script that captures all dashboard tabs."""
    return (
        "import asyncio\n"
        "import os\n"
        "from playwright.async_api import async_playwright\n"
        f"OUTPUT_DIR = {str(output_dir)!r}\n"
        "os.makedirs(OUTPUT_DIR, exist_ok=True)\n"
        "async def main():\n"
        "    async with async_playwright() as pw:\n"
        "        browser = await pw.chromium.launch(headless=True)\n"
        "        context = await browser.new_context(\n"
        f"            viewport={{'width': {width}, 'height': {height}}},\n"
        "            device_scale_factor=2,\n"
        "        )\n"
        "        page = await context.new_page()\n"
        f"        await page.goto({url!r}, wait_until='networkidle', timeout=60000)\n"
        "        await page.wait_for_timeout(3000)\n"
        "        tabs = await page.query_selector_all('[role=\"tab\"]')\n"
        "        if not tabs:\n"
        "            tabs = await page.query_selector_all('[data-testid*=\"tab\"]')\n"
        "        paths = []\n"
        "        if tabs:\n"
        "            for idx, tab in enumerate(tabs):\n"
        "                try:\n"
        "                    await tab.click()\n"
        "                    await page.wait_for_timeout(2500)\n"
        "                except Exception:\n"
        "                    pass\n"
        "                path = os.path.join(OUTPUT_DIR, f'tab_{idx:02d}.png')\n"
        "                await page.screenshot(path=path, full_page=True)\n"
        "                paths.append(path)\n"
        "        else:\n"
        "            path = os.path.join(OUTPUT_DIR, 'full.png')\n"
        "            await page.screenshot(path=path, full_page=True)\n"
        "            paths.append(path)\n"
        "        await browser.close()\n"
        "asyncio.run(main())\n"
    )


def _capture_in_subprocess(url: str, output_dir: Path, width: int, height: int) -> None:
    """Run the capture script in a subprocess."""
    script = _build_capture_script(url, output_dir, width, height)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(f"Playwright subprocess failed: {stderr[:400]}")


async def capture_dashboard_screenshots(
    dashboard_url: str,
    prefix: str,
    width: int = 1600,
    height: int = 1200,
) -> list[str]:
    """
    Capture all tabs of a dashboard as PNG files.

    Returns:
        List of absolute PNG paths (one per tab). Empty list on failure.
    """
    if not dashboard_url or not dashboard_url.strip():
        log_error("screenshot: empty URL")
        return []

    base_dir = _ensure_dir()
    run_dir = base_dir / prefix
    if run_dir.exists():
        for old_file in run_dir.glob("*.png"):
            try:
                old_file.unlink()
            except Exception:
                pass
    run_dir.mkdir(parents=True, exist_ok=True)

    log_process(f"screenshot: capturing {dashboard_url}")

    import asyncio
    try:
        await asyncio.to_thread(
            _capture_in_subprocess, dashboard_url, run_dir, width, height
        )
    except Exception as exc:
        log_error(f"screenshot: failed: {exc}")
        return []

    paths = sorted(str(p.resolve()) for p in run_dir.glob("*.png"))
    if not paths:
        log_error("screenshot: no files produced")
        return []

    log_success(f"screenshot: captured {len(paths)} image(s)")
    return paths