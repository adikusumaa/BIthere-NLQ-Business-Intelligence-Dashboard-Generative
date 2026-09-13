"""
Professional HTML email templates for BIthere reports.

Design constraints:
- No emojis.
- Only bold, italic, and font size variations.
- Table-based layout for maximum email client compatibility.
- Inline CSS (email clients strip <style> tags).
"""

from datetime import datetime


BRAND_NAME = "BIthere"
BRAND_TAGLINE = "AI Business Intelligence Analyst"


def _footer() -> str:
    """Standard footer for all BIthere emails."""
    year = datetime.now().year
    return f"""
    <tr>
      <td style="padding: 24px 32px; background-color: #f4f5f7;
                 border-top: 1px solid #e1e4e8;
                 font-family: Arial, Helvetica, sans-serif;
                 font-size: 12px; color: #6a737d; line-height: 1.6;">
        <p style="margin: 0 0 4px 0;">
          This report was generated automatically by {BRAND_NAME}.
        </p>
        <p style="margin: 0; color: #959da5;">
          &copy; {year} {BRAND_NAME}. All rights reserved.
        </p>
      </td>
    </tr>
    """


def render_report_email(
    title: str,
    insight: str,
    dashboard_url: str | None = None,
) -> str:
    """
    Render a professional HTML email for a BIthere report.

    Args:
        title: Report title (e.g., "Fraud Analysis - January 2010").
        insight: The insight text (may contain newlines; will be converted to paragraphs).
        dashboard_url: Optional link to the Metabase dashboard.

    Returns:
        Full HTML string ready to send.
    """
    paragraphs = "".join(
        f'<p style="margin: 0 0 12px 0; line-height: 1.7;">{line.strip()}</p>'
        for line in insight.split("\n")
        if line.strip()
    )

    dashboard_block = ""
    if dashboard_url:
        dashboard_block = f"""
        <tr>
          <td style="padding: 0 32px 24px 32px;">
            <a href="{dashboard_url}"
               style="display: inline-block;
                      padding: 10px 20px;
                      background-color: #1f6feb;
                      color: #ffffff;
                      text-decoration: none;
                      border-radius: 4px;
                      font-family: Arial, Helvetica, sans-serif;
                      font-size: 14px;
                      font-weight: bold;">
              View Dashboard
            </a>
          </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f5f7;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background-color: #f4f5f7; padding: 32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               style="background-color: #ffffff;
                      border-radius: 8px;
                      overflow: hidden;
                      border: 1px solid #e1e4e8;">

          <tr>
            <td style="padding: 24px 32px; background-color: #0d1117;
                       border-bottom: 1px solid #30363d;">
              <p style="margin: 0; font-family: Arial, Helvetica, sans-serif;
                        font-size: 20px; font-weight: bold; color: #ffffff;">
                {BRAND_NAME}
              </p>
              <p style="margin: 4px 0 0 0; font-family: Arial, Helvetica, sans-serif;
                        font-size: 12px; color: #8b949e;">
                {BRAND_TAGLINE}
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding: 32px 32px 8px 32px;">
              <h1 style="margin: 0; font-family: Arial, Helvetica, sans-serif;
                         font-size: 20px; font-weight: bold; color: #0d1117;">
                {title}
              </h1>
            </td>
          </tr>

          <tr>
            <td style="padding: 16px 32px 8px 32px; font-family: Arial, Helvetica, sans-serif;
                       font-size: 14px; color: #24292f;">
              {paragraphs}
            </td>
          </tr>

          {dashboard_block}

          {_footer()}

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def render_report_subject(topic: str, period: str | None = None) -> str:
    """
    Standard subject line convention for BIthere reports.

    Example: "[BIthere] Fraud Analysis - January 2010"
    """
    if period:
        return f"[{BRAND_NAME}] {topic} - {period}"
    return f"[{BRAND_NAME}] {topic}"