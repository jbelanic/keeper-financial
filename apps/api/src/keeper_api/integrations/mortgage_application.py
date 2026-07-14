from __future__ import annotations

import re
from urllib.parse import urlparse

from keeper_api.core.config import Settings


class MortgageApplicationUnavailable(ValueError):
    pass


_AGENT_SLUG = re.compile(r"^[a-z0-9-]{1,100}$")


class MortgageApplicationAdapter:
    """Configuration-only redirect boundary; no vendor API is implemented in Phase 0."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def redirect_url(self, agent_slug: str | None = None) -> str:
        if self.settings.mortgage_application_provider == "disabled":
            raise MortgageApplicationUnavailable("external mortgage application is not configured")
        url = self.settings.mortgage_application_url
        if agent_slug is not None:
            if not _AGENT_SLUG.fullmatch(agent_slug):
                raise MortgageApplicationUnavailable("agent attribution is invalid")
            url = self.settings.mortgage_application_agent_links.get(agent_slug)
            if url is None:
                raise MortgageApplicationUnavailable(
                    "agent-specific application link is not configured"
                )
        if not url:
            raise MortgageApplicationUnavailable("external mortgage application is not configured")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise MortgageApplicationUnavailable("application destination must use HTTPS")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise MortgageApplicationUnavailable(
                "application destination must not contain credentials or query data"
            )
        if parsed.hostname.lower() not in self.settings.allowed_mortgage_hosts:
            raise MortgageApplicationUnavailable("application destination host is not allow-listed")
        return url
