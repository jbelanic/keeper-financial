from __future__ import annotations

from email.message import EmailMessage
from typing import ClassVar

import pytest
from pydantic import SecretStr

from keeper_api.core.config import Settings
from keeper_api.services.borrower_notifications import send_assignment_email


class FakeSMTP:
    messages: ClassVar[list[EmailMessage]] = []
    login_attempts: ClassVar[list[tuple[str, str]]] = []

    def __init__(self, host: str, port: int, timeout: int = 10) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def __enter__(self) -> FakeSMTP:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def starttls(self) -> None:
        return None

    def login(self, user: str, password: str) -> None:
        self.login_attempts.append((user, password))

    def send_message(self, message: EmailMessage) -> None:
        self.messages.append(message)


def _sent_application_id() -> str:
    return "00000000-0000-4000-8000-000000000001"


def test_assignment_email_authenticates_when_smtp_credentials_set(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.smtp_enabled = True
    settings.smtp_host = "mail.smtp2go.com"
    settings.smtp_port = 587
    settings.smtp_use_tls = True
    settings.smtp_username = "smtp2go-user"
    settings.smtp_password = SecretStr("smtp2go-password")
    FakeSMTP.messages = []
    FakeSMTP.login_attempts = []
    monkeypatch.setattr("keeper_api.services.borrower_notifications.smtplib.SMTP", FakeSMTP)

    sent = send_assignment_email(
        settings=settings,
        agent_name="Synthetic Agent",
        agent_email="agent@example.test",
        application_id=_sent_application_id(),
    )

    assert sent is True
    assert FakeSMTP.login_attempts == [("smtp2go-user", "smtp2go-password")]
    assert len(FakeSMTP.messages) == 1
    assert FakeSMTP.messages[0]["To"] == "agent@example.test"


def test_assignment_email_skips_login_without_credentials(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.smtp_enabled = True
    settings.smtp_host = "127.0.0.1"
    settings.smtp_port = 1025
    settings.smtp_use_tls = False
    settings.smtp_username = None
    settings.smtp_password = None
    FakeSMTP.messages = []
    FakeSMTP.login_attempts = []
    monkeypatch.setattr("keeper_api.services.borrower_notifications.smtplib.SMTP", FakeSMTP)

    sent = send_assignment_email(
        settings=settings,
        agent_name="Synthetic Agent",
        agent_email="agent@example.test",
        application_id=_sent_application_id(),
    )

    assert sent is True
    assert FakeSMTP.login_attempts == []
    assert len(FakeSMTP.messages) == 1
    assert FakeSMTP.messages[0]["To"] == "agent@example.test"


def test_assignment_email_returns_false_when_smtp_disabled(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings.smtp_enabled = False
    FakeSMTP.messages = []
    FakeSMTP.login_attempts = []
    monkeypatch.setattr("keeper_api.services.borrower_notifications.smtplib.SMTP", FakeSMTP)

    sent = send_assignment_email(
        settings=settings,
        agent_name="Synthetic Agent",
        agent_email="agent@example.test",
        application_id=_sent_application_id(),
    )

    assert sent is False
    assert FakeSMTP.messages == []
    assert FakeSMTP.login_attempts == []
