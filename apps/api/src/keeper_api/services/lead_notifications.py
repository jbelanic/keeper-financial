from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings
from keeper_api.models.domain import AgentProfile, LeadInquiry, User

logger = logging.getLogger(__name__)

ADMIN_LEADS_PATH = "https://keeperfinancial.ca/admin/leads"


def _recipient_message(
    *,
    settings: Settings,
    recipient_email: str,
    recipient_label: str,
    lead: LeadInquiry,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient_email
    message["Subject"] = settings.lead_notification_subject
    preferred_agent = lead.preferred_agent_slug or "none selected"
    text = (
        "A new Keeper contact request has been received.\n\n"
        f"Notification recipient: {recipient_label}\n"
        f"Lead reference: {lead.id}\n"
        f"Status: {lead.status}\n"
        f"Source: {lead.source}\n"
        f"Preferred agent: {preferred_agent}\n\n"
        f"Review the request in the protected admin lead queue:\n{ADMIN_LEADS_PATH}\n\n"
        "No applicant name, email address, phone number, or free-text message is included "
        "in this notification.\n"
    )
    html = (
        "<p>A new Keeper contact request has been received.</p>"
        f"<p><strong>Notification recipient:</strong> {recipient_label}</p>"
        f"<p><strong>Lead reference:</strong> <code>{lead.id}</code></p>"
        f"<p><strong>Status:</strong> {lead.status}<br />"
        f"<strong>Source:</strong> {lead.source}<br />"
        f"<strong>Preferred agent:</strong> {preferred_agent}</p>"
        f'<p>Review the request in the protected <a href="{ADMIN_LEADS_PATH}">admin lead queue</a>.</p>'
        "<p>No applicant name, email address, phone number, or free-text message is included "
        "in this notification.</p>"
    )
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    return message


def _agent_email_for_lead(db: Session, lead: LeadInquiry) -> str | None:
    if not lead.preferred_agent_slug:
        return None
    return db.scalar(
        select(User.email)
        .join(AgentProfile, AgentProfile.user_id == User.id)
        .where(
            AgentProfile.slug == lead.preferred_agent_slug,
            AgentProfile.status == "published",
            User.is_active.is_(True),
        )
    )


def _notification_recipients(
    db: Session, settings: Settings, lead: LeadInquiry
) -> list[tuple[str, str]]:
    recipients: list[tuple[str, str]] = []
    agent_email = _agent_email_for_lead(db, lead)
    if agent_email:
        recipients.append((agent_email, "selected agent"))
    elif settings.lead_notification_broker_email:
        recipients.append((settings.lead_notification_broker_email, "broker of record"))
    if settings.lead_notification_admin_email:
        recipients.append((settings.lead_notification_admin_email, "brokerage administrator"))
    return recipients


def send_lead_notification_emails(
    db: Session,
    *,
    settings: Settings,
    lead: LeadInquiry,
) -> int:
    """Send non-blocking, PII-minimized notifications for a new contact lead."""

    if not settings.lead_notification_email_enabled:
        logger.info("Lead notification email disabled; skipping lead %s", lead.id)
        return 0
    if not settings.smtp_enabled:
        logger.info("SMTP disabled; skipping lead notification email for %s", lead.id)
        return 0

    sent = 0
    for recipient_email, recipient_label in _notification_recipients(db, settings, lead):
        try:
            message = _recipient_message(
                settings=settings,
                recipient_email=recipient_email,
                recipient_label=recipient_label,
                lead=lead,
            )
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.send_message(message)
            sent += 1
        except Exception:
            logger.exception(
                "Failed to send lead notification email for %s to %s; lead submission continues",
                lead.id,
                recipient_label,
            )
    return sent
