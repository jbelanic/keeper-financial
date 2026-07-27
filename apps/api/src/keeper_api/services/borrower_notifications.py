from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import urljoin

from keeper_api.core.config import Settings

logger = logging.getLogger(__name__)

# External application host used only to build a sign-in link in the email.
# Borrower PII is never included in the notification.
AGENT_PORTAL_HOST = "https://apply.keeperfinancial.ca"


def build_assignment_email(
    *,
    settings: Settings,
    agent_name: str,
    agent_email: str,
    application_id: str,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = agent_email
    message["Subject"] = settings.smtp_notification_subject

    agent_name = agent_name or "Agent"
    portal_url = urljoin(f"{AGENT_PORTAL_HOST}/", "agent")
    text = (
        f"Hello {agent_name},\n\n"
        f"A borrower mortgage application has been assigned to you for review.\n\n"
        f"Application reference: {application_id}\n\n"
        f"Sign in to your agent workspace to review the submitted application "
        f"and retrieve the details needed to open the deal:\n{portal_url}\n\n"
        f"This is an automated notification. Please do not reply.\n"
    )
    html = (
        f"<p>Hello {agent_name},</p>"
        f"<p>A borrower mortgage application has been assigned to you for review.</p>"
        f"<p>Application reference: <code>{application_id}</code></p>"
        f'<p>Sign in to your <a href="{portal_url}">agent workspace</a> to review '
        f"the submitted application and retrieve the details needed to open the deal.</p>"
        f"<p>This is an automated notification. Please do not reply.</p>"
    )
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    return message


def send_assignment_email(
    *,
    settings: Settings,
    agent_name: str,
    agent_email: str,
    application_id: str,
) -> bool:
    """Send a single transactional assignment notification.

    Returns True when sent, False when disabled or on any mail failure. Mail
    failures must never abort the assignment transaction, so all errors are
    caught and logged here.
    """
    if not settings.smtp_enabled:
        logger.info("SMTP disabled; skipping assignment email for %s", application_id)
        return False
    if not agent_email:
        logger.warning("No agent email; skipping assignment email for %s", application_id)
        return False

    try:
        message = build_assignment_email(
            settings=settings,
            agent_name=agent_name,
            agent_email=agent_email,
            application_id=application_id,
        )
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.send_message(message)
        logger.info("Sent assignment email to agent for %s", application_id)
        return True
    except Exception:  # mail must not fail the assignment
        logger.exception(
            "Failed to send assignment email for %s; assignment continues",
            application_id,
        )
        return False
