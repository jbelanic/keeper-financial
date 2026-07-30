from __future__ import annotations

import json
import logging
import smtplib
from email.message import EmailMessage
from urllib import error, request

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


def _smtp_host_candidates(settings: Settings) -> list[str]:
    candidates = [settings.smtp_host]
    if settings.app_env == "local" and settings.smtp_host == "host.docker.internal":
        candidates.append("127.0.0.1")
    return candidates


def _mailpit_http_urls(settings: Settings) -> list[str]:
    if settings.app_env != "local" or settings.smtp_port != 54324:
        return []
    return [f"http://{host}:{settings.smtp_port}/api/v1/send" for host in _smtp_host_candidates(settings)]


def _message_body(message: EmailMessage, content_type: str) -> str:
    if message.is_multipart():
        return "\n".join(
            part.get_content()
            for part in message.iter_parts()
            if part.get_content_type() == content_type
        )
    return message.get_content() if message.get_content_type() == content_type else ""


def _send_via_mailpit_http_api(
    *,
    settings: Settings,
    recipient_email: str,
    message: EmailMessage,
) -> bool:
    payload = {
        "From": {"Email": settings.smtp_from},
        "To": [{"Email": recipient_email}],
        "Subject": str(message["Subject"]),
        "Text": _message_body(message, "text/plain"),
        "HTML": _message_body(message, "text/html"),
        "Tags": ["keeper-local-lead-notification"],
    }
    body = json.dumps(payload).encode("utf-8")
    urls = _mailpit_http_urls(settings)
    for url in urls:
        try:
            api_request = request.Request(  # noqa: S310 - local-only http:// Mailpit URLs are constructed above.
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(api_request, timeout=10) as response:  # noqa: S310
                if 200 <= response.status < 300:
                    return True
        except (OSError, error.HTTPError, error.URLError):
            if url == urls[-1]:
                raise
            logger.info("Local Mailpit HTTP endpoint %s unavailable; trying fallback", url)
    return False


def _send_message(
    *, settings: Settings, recipient_email: str, message: EmailMessage
) -> None:
    if _send_via_mailpit_http_api(
        settings=settings, recipient_email=recipient_email, message=message
    ):
        return
    smtp_hosts = _smtp_host_candidates(settings)
    for smtp_host in smtp_hosts:
        try:
            with smtplib.SMTP(smtp_host, settings.smtp_port, timeout=10) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.send_message(message)
            return
        except (OSError, smtplib.SMTPException):
            if smtp_host == smtp_hosts[-1]:
                raise
            logger.info(
                "Lead notification SMTP host %s unavailable; trying local fallback",
                smtp_host,
            )


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
            _send_message(settings=settings, recipient_email=recipient_email, message=message)
            sent += 1
        except Exception:
            logger.exception(
                "Failed to send lead notification email for %s to %s; lead submission continues",
                lead.id,
                recipient_label,
            )
    return sent
