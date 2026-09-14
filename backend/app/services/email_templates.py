"""
Professional email templates for BIthere reports.
Uses SF Pro (Apple system font) with fallback stack.
Compact layout with signature.
"""

import html as html_lib
import re
from datetime import datetime


BRAND_NAME = "BIthere"
BRAND_TAGLINE = "AI Business Intelligence Analyst"

FONT_STACK = (
    "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', "
    "'Helvetica Neue', Helvetica, Arial, sans-serif"
)


_INLINE_PATTERNS = [
    (re.compile(r"\*\*(.+?)\*\*", re.DOTALL), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", re.DOTALL), r"<em>\1</em>"),
    (re.compile(r"`(.+?)`"), r'<code style="background:#f2f2f7;padding:1px 5px;'
                             r'border-radius:3px;font-size:12px;">\1</code>'),
    (re.compile(r"\[(.+?)\]\((.+?)\)"),
     r'<a href="\2" style="color:#0071e3;text-decoration:none;">\1</a>'),
]


def _render_inline(text: str) -> str:
    escaped = html_lib.escape(text, quote=False)
    for pattern, repl in _INLINE_PATTERNS:
        escaped = pattern.sub(repl, escaped)
    return escaped


def _render_blocks(text: str) -> str:
    """Convert text into compact HTML paragraphs and lists."""
    if not text:
        return ""

    lines = text.split("\n")
    blocks: list[str] = []
    list_buffer: list[str] = []
    list_type: str | None = None

    def flush_list() -> None:
        nonlocal list_buffer, list_type
        if not list_buffer:
            return
        tag = "ol" if list_type == "ol" else "ul"
        style = (
            f"margin:0 0 14px 0;padding-left:20px;line-height:1.6;"
            f"color:#1d1d1f;font-size:14px;"
        )
        items = "".join(
            f'<li style="margin:0 0 5px 0;">{item}</li>' for item in list_buffer
        )
        blocks.append(f'<{tag} style="{style}">{items}</{tag}>')
        list_buffer = []
        list_type = None

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_list()
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            if list_type and list_type != "ol":
                flush_list()
            list_type = "ol"
            list_buffer.append(_render_inline(numbered.group(2)))
            continue

        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet and not stripped.startswith("**"):
            if list_type and list_type != "ul":
                flush_list()
            list_type = "ul"
            list_buffer.append(_render_inline(bullet.group(1)))
            continue

        header = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if header:
            flush_list()
            level = len(header.group(1))
            size = {1: 16, 2: 15, 3: 14}.get(level, 14)
            margin_top = 4 if blocks else 0
            blocks.append(
                f'<h{level + 1} style="margin:{margin_top}px 0 8px 0;'
                f'font-family:{FONT_STACK};'
                f'font-size:{size}px;font-weight:600;'
                f'color:#1d1d1f;line-height:1.35;letter-spacing:-0.01em;">'
                f"{_render_inline(header.group(2))}</h{level + 1}>"
            )
            continue

        # Short line ending with colon -> bold subheading
        if (
            len(stripped) < 60
            and stripped.endswith(":")
            and not stripped.endswith("::")
        ):
            flush_list()
            blocks.append(
                f'<p style="margin:12px 0 6px 0;font-family:{FONT_STACK};'
                f'font-size:13px;font-weight:600;color:#1d1d1f;">'
                f"{_render_inline(stripped[:-1])}</p>"
            )
            continue

        flush_list()
        blocks.append(
            f'<p style="margin:0 0 10px 0;line-height:1.6;'
            f'color:#1d1d1f;font-size:14px;letter-spacing:-0.01em;">'
            f"{_render_inline(stripped)}</p>"
        )

    flush_list()
    return "".join(blocks)


def _header_block() -> str:
    return f"""
    <tr>
      <td style="padding:20px 32px;background-color:#1d1d1f;">
        <p style="margin:0;font-family:{FONT_STACK};
                  font-size:18px;font-weight:600;color:#ffffff;
                  letter-spacing:-0.02em;">
          {BRAND_NAME}
        </p>
        <p style="margin:4px 0 0 0;font-family:{FONT_STACK};
                  font-size:11px;color:#a1a1a6;letter-spacing:0.02em;">
          {BRAND_TAGLINE}
        </p>
      </td>
    </tr>
    """


def _metadata_block(report_id: str | None = None) -> str:
    now = datetime.now()
    rid = report_id or f"BIT-{now.strftime('%Y%m%d-%H%M%S')}"
    date_str = now.strftime("%d %B %Y")
    return f"""
    <tr>
      <td style="padding:12px 32px;background-color:#f5f5f7;
                 border-bottom:1px solid #d2d2d7;">
        <p style="margin:0;font-family:{FONT_STACK};
                  font-size:11px;color:#6e6e73;line-height:1.6;
                  letter-spacing:0.01em;">
          <strong style="color:#1d1d1f;font-weight:600;">{rid}</strong>
          &nbsp;&middot;&nbsp;{date_str}
          &nbsp;&middot;&nbsp;Internal Use
        </p>
      </td>
    </tr>
    """


def _title_block(title: str) -> str:
    return f"""
    <tr>
      <td style="padding:24px 32px 4px 32px;">
        <h1 style="margin:0;font-family:{FONT_STACK};
                   font-size:22px;font-weight:600;color:#1d1d1f;
                   line-height:1.3;letter-spacing:-0.02em;">
          {html_lib.escape(title)}
        </h1>
      </td>
    </tr>
    """


def _body_block(insight: str) -> str:
    return f"""
    <tr>
      <td style="padding:14px 32px 6px 32px;font-family:{FONT_STACK};">
        {_render_blocks(insight)}
      </td>
    </tr>
    """


def _screenshots_block(screenshot_urls: list[str] | None) -> str:
    if not screenshot_urls:
        return ""
    parts = []
    for idx, url in enumerate(screenshot_urls, start=1):
        parts.append(
            f"""
            <tr>
              <td style="padding:10px 32px 16px 32px;">
                <p style="margin:0 0 6px 0;font-family:{FONT_STACK};
                          font-size:10px;color:#6e6e73;
                          letter-spacing:0.08em;text-transform:uppercase;
                          font-weight:600;">
                  Exhibit {idx} &middot; Dashboard View
                </p>
                <img src="{url}" alt="Dashboard view {idx}"
                     style="display:block;width:100%;max-width:100%;
                            border:1px solid #d2d2d7;border-radius:6px;" />
              </td>
            </tr>
            """
        )
    return "".join(parts)


def _dashboard_link_block(dashboard_url: str | None) -> str:
    if not dashboard_url:
        return ""
    return f"""
    <tr>
      <td style="padding:6px 32px 20px 32px;">
        <a href="{dashboard_url}"
           style="display:inline-block;padding:9px 18px;
                  background-color:#0071e3;color:#ffffff;
                  text-decoration:none;border-radius:980px;
                  font-family:{FONT_STACK};
                  font-size:13px;font-weight:500;
                  letter-spacing:-0.01em;">
          Open Dashboard
        </a>
      </td>
    </tr>
    """


def _signature_block() -> str:
    return f"""
    <tr>
      <td style="padding:8px 32px 24px 32px;
                 border-top:1px solid #e5e5ea;">
        <p style="margin:14px 0 0 0;font-family:{FONT_STACK};
                  font-size:13px;color:#1d1d1f;line-height:1.5;">
          Best regards,
        </p>
        <p style="margin:2px 0 0 0;font-family:{FONT_STACK};
                  font-size:13px;font-weight:600;color:#1d1d1f;">
          BIthere Analyst
        </p>
        <p style="margin:2px 0 0 0;font-family:{FONT_STACK};
                  font-size:12px;color:#6e6e73;">
          Business Intelligence Team
        </p>
      </td>
    </tr>
    """


def _footer_block() -> str:
    year = datetime.now().year
    return f"""
    <tr>
      <td style="padding:16px 32px 20px 32px;background-color:#f5f5f7;
                 border-top:1px solid #d2d2d7;">
        <p style="margin:0;font-family:{FONT_STACK};
                  font-size:11px;color:#6e6e73;line-height:1.5;">
          Generated automatically by {BRAND_NAME}.
          &nbsp;&middot;&nbsp;&copy; {year} {BRAND_NAME}.
        </p>
      </td>
    </tr>
    """


def render_report_email(
    title: str,
    insight: str,
    dashboard_url: str | None = None,
    screenshot_urls: list[str] | None = None,
    report_id: str | None = None,
) -> str:
    """Render a compact, consultant-grade HTML report email."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{html_lib.escape(title)}</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f7;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background-color:#f5f5f7;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="680" cellpadding="0" cellspacing="0"
               style="background-color:#ffffff;border:1px solid #d2d2d7;
                      border-radius:12px;overflow:hidden;">
          {_header_block()}
          {_metadata_block(report_id)}
          {_title_block(title)}
          {_body_block(insight)}
          {_screenshots_block(screenshot_urls)}
          {_dashboard_link_block(dashboard_url)}
          {_signature_block()}
          {_footer_block()}
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def render_report_subject(topic: str, period: str | None = None) -> str:
    if period:
        return f"[{BRAND_NAME}] {topic} - {period}"
    return f"[{BRAND_NAME}] {topic}"