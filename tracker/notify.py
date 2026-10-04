"""Optional email of the daily digest. Configure via SMTP_* and DIGEST_TO environment variables."""

import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger(__name__)


def send_digest(markdown_text, subject, site_url=""):
    host, to = os.environ.get("SMTP_HOST"), os.environ.get("DIGEST_TO")
    if not host or not to:
        log.info("SMTP_HOST/DIGEST_TO not set - not emailing digest")
        return False
    body = markdown_text + (f"\n\nDashboard: {site_url}\n" if site_url else "")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER") or "freezone-ai-watch@localhost"
    msg["To"] = to
    msg.set_content(body)
    port = int(os.environ.get("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            if os.environ.get("SMTP_USER"):
                smtp.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
            smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        log.warning("digest email failed: %s", exc)
        return False
    log.info("digest emailed to %s", to)
    return True
