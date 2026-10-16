#!/usr/bin/env python3
"""Send a plain-text operational alert email (decision 49 P0).

Reuses the authenticated SMTP path (SMTP2GO). Reads SMTP settings and
``ALERT_EMAIL`` from the environment, loading the project ``.env`` when present.
The SMTP password and message body are never logged; only a safe outcome line is
printed.

Usage:
  echo "backup failed" | .venv/bin/python scripts/send_alert.py "Keeper backup FAILED"

Exit codes: 0 = sent; 1 = send failed; 2 = misconfigured (no ALERT_EMAIL).
"""

from __future__ import annotations

import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path


def _load_env() -> None:
    """Load the deployment environment file (see ``keeper_api.services.ops_env``)."""
    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "apps" / "api" / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    from keeper_api.services.ops_env import load_env_file

    load_env_file(root=repo_root)


def main(argv: list[str]) -> int:
    _load_env()
    subject = argv[0] if argv else "Keeper operational alert"
    body = sys.stdin.read().strip() or "(no detail)"

    alert_email = os.environ.get("ALERT_EMAIL", "").strip()
    if not alert_email:
        print("send-alert: ALERT_EMAIL is not set; cannot send alert", file=sys.stderr)
        return 2

    host = os.environ.get("SMTP_HOST", "127.0.0.1")
    port = int(os.environ.get("SMTP_PORT", "54324"))
    sender = os.environ.get("SMTP_FROM", "no-reply@keeperfinancial.ca")
    username = os.environ.get("SMTP_USERNAME") or None
    password = os.environ.get("SMTP_PASSWORD") or None
    use_tls = os.environ.get("SMTP_USE_TLS", "false").lower() in {"1", "true", "yes"}

    message = EmailMessage()
    message["From"] = sender
    message["To"] = alert_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        print(f"send-alert: send failed: {exc}", file=sys.stderr)
        return 1

    print(f"ALERT_SENT to={alert_email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
