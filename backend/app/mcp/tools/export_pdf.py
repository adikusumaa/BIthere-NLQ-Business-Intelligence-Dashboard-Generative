"""
MCP tool: export_pdf
Convert a report to PDF.

Primary engine:  WeasyPrint (per PRJ tech stack).
Fallback engine: FPDF2 (pure Python, for Windows without GTK).

Supports an optional dashboard screenshot embedded in the report.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import log_process, log_success, log_error, log_warning
from app.services.email_templates import render_report_email


REPORTS_DIR = Path("reports")

PAGE_WIDTH_MM = 210
MARGIN_MM = 20
CONTENT_WIDTH_MM = PAGE_WIDTH_MM - (2 * MARGIN_MM)

COLOR_DARK = (13, 17, 23)
COLOR_TEXT = (40, 40, 40)
COLOR_MUTED = (120, 120, 120)
COLOR_RULE = (200, 200, 200)
COLOR_LINK = (31, 111, 235)
COLOR_WHITE = (255, 255, 255)
COLOR_LIGHT = (200, 200, 200)


def _ensure_reports_dir() -> Path:
    """Ensure the reports output directory exists."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def _build_filename(title: str, ext: str = "pdf") -> str:
    """Build a safe, timestamped filename."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
    safe = safe.strip("_")[:60] or "report"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe}_{stamp}.{ext}"


def _html_to_pdf_weasyprint(html: str, output_path: Path) -> None:
    """Render HTML to PDF using WeasyPrint (requires GTK)."""
    from weasyprint import HTML

    HTML(string=html).write_pdf(str(output_path))


def _is_section_header(text: str) -> bool:
    """Heuristic: a short line ending with colon is a section header."""
    stripped = text.strip()
    if not stripped or len(stripped) > 60:
        return False
    return stripped.endswith(":") or stripped.isupper()


def _render_header_block(pdf) -> None:
    """Draw the brand header block at the top of the first page."""
    pdf.set_fill_color(*COLOR_DARK)
    pdf.rect(0, 0, PAGE_WIDTH_MM, 28, style="F")

    pdf.set_xy(MARGIN_MM, 8)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*COLOR_WHITE)
    pdf.cell(0, 8, "BIthere", ln=True)

    pdf.set_xy(MARGIN_MM, 17)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COLOR_LIGHT)
    pdf.cell(0, 5, "AI Business Intelligence Analyst", ln=True)


def _render_metadata_block(pdf) -> None:
    """Draw the report metadata block."""
    now = datetime.now()
    report_id = f"BIT-{now.strftime('%Y%m%d-%H%M%S')}"
    generated = now.strftime("%d %B %Y, %H:%M")

    pdf.set_y(34)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*COLOR_MUTED)

    pdf.set_x(MARGIN_MM)
    pdf.cell(0, 4, f"Report ID: {report_id}", ln=True)
    pdf.set_x(MARGIN_MM)
    pdf.cell(0, 4, f"Generated: {generated}", ln=True)
    pdf.set_x(MARGIN_MM)
    pdf.cell(0, 4, "Classification: Confidential", ln=True)

    pdf.ln(2)
    pdf.set_draw_color(*COLOR_RULE)
    pdf.line(MARGIN_MM, pdf.get_y(), PAGE_WIDTH_MM - MARGIN_MM, pdf.get_y())
    pdf.ln(6)


def _render_title(pdf, title: str) -> None:
    """Draw the main report title."""
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*COLOR_DARK)
    pdf.multi_cell(0, 8, title)
    pdf.ln(2)

    pdf.set_draw_color(*COLOR_DARK)
    pdf.set_line_width(0.4)
    pdf.line(MARGIN_MM, pdf.get_y(), PAGE_WIDTH_MM - MARGIN_MM, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(6)


def _render_body(pdf, insight: str) -> None:
    """Render the body with section header detection."""
    paragraphs = [p.strip() for p in insight.split("\n") if p.strip()]

    for para in paragraphs:
        if _is_section_header(para):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*COLOR_DARK)
            pdf.multi_cell(0, 6, para.rstrip(":"))
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.multi_cell(0, 5.5, para, align="J")
            pdf.ln(3)


def _render_kpi_table(pdf, kpis: list[dict] | None) -> None:
    """Render a key metrics table."""
    if not kpis:
        return

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(0, 6, "Key Metrics", ln=True)
    pdf.ln(2)

    col_w_label = 90
    col_w_value = CONTENT_WIDTH_MM - col_w_label

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(col_w_label, 7, "  Metric", border=0, fill=True)
    pdf.cell(col_w_value, 7, "Value", border=0, fill=True, align="R")
    pdf.ln(7)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*COLOR_TEXT)
    for kpi in kpis:
        label = str(kpi.get("label", ""))
        value = str(kpi.get("value", ""))
        pdf.cell(col_w_label, 6, f"  {label}", border="B")
        pdf.cell(col_w_value, 6, value, border="B", align="R")
        pdf.ln(6)

    pdf.ln(4)


def _render_dashboard_section(
    pdf,
    dashboard_url: str,
    screenshot_path: str | None,
) -> None:
    """Render the dashboard section with optional embedded image."""
    pdf.ln(2)
    pdf.set_draw_color(*COLOR_RULE)
    pdf.line(MARGIN_MM, pdf.get_y(), PAGE_WIDTH_MM - MARGIN_MM, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_DARK)
    pdf.cell(0, 6, "Interactive Dashboard", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.multi_cell(
        0, 5.5,
        "The full interactive version of this report is available at the "
        "URL below. Open it in a browser to filter and explore the charts.",
        align="J",
    )
    pdf.ln(2)

    pdf.set_font("Helvetica", "U", 9)
    pdf.set_text_color(*COLOR_LINK)
    pdf.multi_cell(0, 5, dashboard_url, link=dashboard_url)
    pdf.ln(4)

    if screenshot_path and Path(screenshot_path).exists():
        try:
            available_w = CONTENT_WIDTH_MM
            pdf.image(screenshot_path, x=MARGIN_MM, w=available_w)
            pdf.ln(3)
        except Exception as exc:
            log_warning(f"export_pdf: image embed failed: {exc}")


def _render_footer(pdf) -> None:
    """Draw the footer with copyright."""
    pdf.set_y(-22)
    pdf.set_draw_color(*COLOR_RULE)
    pdf.line(MARGIN_MM, pdf.get_y(), PAGE_WIDTH_MM - MARGIN_MM, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*COLOR_MUTED)
    year = datetime.now().year
    pdf.cell(
        0, 4,
        f"(c) {year} BIthere. All rights reserved. "
        f"This report was generated automatically.",
        align="C",
    )


def _text_to_pdf_fpdf(
    title: str,
    insight: str,
    dashboard_url: str | None,
    kpis: list[dict] | None,
    screenshot_path: str | None,
    output_path: Path,
) -> None:
    """Render the professional PDF report using FPDF2."""
    from fpdf import FPDF

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_margins(MARGIN_MM, MARGIN_MM, MARGIN_MM)
    pdf.add_page()

    _render_header_block(pdf)
    _render_metadata_block(pdf)
    _render_title(pdf, title)
    _render_body(pdf, insight)
    _render_kpi_table(pdf, kpis)

    if dashboard_url:
        _render_dashboard_section(pdf, dashboard_url, screenshot_path)

    _render_footer(pdf)
    pdf.output(str(output_path))


def _pdf_fail(message: str) -> dict[str, Any]:
    """Standard failure response."""
    return {
        "success": False,
        "pdf_path": None,
        "filename": None,
        "engine": None,
        "screenshot_path": None,
        "error": message,
    }


async def _render_weasyprint(html: str, output_path: Path) -> None:
    """Async wrapper for the WeasyPrint renderer."""
    await asyncio.to_thread(_html_to_pdf_weasyprint, html, output_path)


async def _render_fpdf(
    title: str,
    insight: str,
    dashboard_url: str | None,
    kpis: list[dict] | None,
    screenshot_path: str | None,
    output_path: Path,
) -> None:
    """Async wrapper for the FPDF2 renderer."""
    await asyncio.to_thread(
        _text_to_pdf_fpdf,
        title,
        insight,
        dashboard_url,
        kpis,
        screenshot_path,
        output_path,
    )


async def export_pdf(
    title: str,
    insight: str,
    dashboard_url: str | None = None,
    kpis: list[dict] | None = None,
    capture_screenshot: bool = False,
) -> dict[str, Any]:
    """
    Export a report to PDF.

    Uses WeasyPrint when available. Falls back to FPDF2 when the
    WeasyPrint native dependencies (GTK) are missing.

    Args:
        title: Report title.
        insight: Main text content. Newlines separate paragraphs.
            Short lines ending with ':' become section headers.
        dashboard_url: Optional dashboard link.
        kpis: Optional list of {"label": str, "value": str} for metrics table.
        capture_screenshot: If True and dashboard_url set, capture a
            screenshot of the dashboard and embed it in the PDF.

    Returns:
        dict with keys: success, pdf_path, filename, engine,
            screenshot_path, error.
    """
    log_process(f"export_pdf: '{title[:40]}'")

    if not title or not title.strip():
        return _pdf_fail("Title is required")
    if not insight or not insight.strip():
        return _pdf_fail("Insight content is required")

    screenshot_path: str | None = None

    if capture_screenshot and dashboard_url:
        from app.services.dashboard_screenshot import (
            capture_dashboard_screenshot,
        )

        ss_filename = _build_filename(title, "png")
        screenshot_path = await capture_dashboard_screenshot(
            dashboard_url, ss_filename
        )
        if screenshot_path:
            log_success(f"export_pdf: screenshot at {screenshot_path}")
        else:
            log_warning("export_pdf: screenshot capture failed, continuing without it")

    _ensure_reports_dir()
    filename = _build_filename(title, "pdf")
    output_path = REPORTS_DIR / filename

    try:
        html = render_report_email(
            title=title,
            insight=insight,
            dashboard_url=dashboard_url,
        )
    except Exception as exc:
        log_error(f"export_pdf: template render failed: {exc}")
        return _pdf_fail(f"Template render failed: {exc}")

    engine = "weasyprint"
    try:
        await _render_weasyprint(html, output_path)
    except Exception as exc:
        log_warning(
            f"export_pdf: WeasyPrint unavailable ({exc}); "
            f"falling back to FPDF2"
        )
        engine = "fpdf2"
        try:
            await _render_fpdf(
                title,
                insight,
                dashboard_url,
                kpis,
                screenshot_path,
                output_path,
            )
        except ImportError:
            return _pdf_fail("Neither WeasyPrint nor FPDF2 is available")
        except Exception as fpdf_exc:
            log_error(f"export_pdf: FPDF2 failed: {fpdf_exc}")
            return _pdf_fail(str(fpdf_exc))

    if not output_path.exists():
        return _pdf_fail("PDF file was not created")

    log_success(f"export_pdf: created {output_path} via {engine}")
    return {
        "success": True,
        "pdf_path": str(output_path.resolve()),
        "filename": filename,
        "engine": engine,
        "screenshot_path": screenshot_path,
        "error": None,
    }