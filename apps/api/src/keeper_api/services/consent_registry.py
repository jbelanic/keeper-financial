from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True)
class ConsentDefinition:
    purpose: str
    wording: str
    wording_version: str


SERVICE_CONTACT_CONSENT: Final = ConsentDefinition(
    purpose="service_contact_acknowledgement",
    wording="I agree that Keeper Financial may contact me about this service inquiry.",
    wording_version="service-contact-draft-engineering-v1",
)
MARKETING_CONSENT: Final = ConsentDefinition(
    purpose="marketing",
    wording=(
        "I would also like optional marketing communications. "
        "This is separate and not required for service."
    ),
    wording_version="marketing-draft-engineering-v1",
)
PRIVACY_NOTICE_VERSION: Final = "privacy-notice-draft-legal-review-v1"
WEBSITE_CAPTURE_SOURCE: Final = "website_apply"

CONSENT_REGISTRY = MappingProxyType(
    {
        SERVICE_CONTACT_CONSENT.purpose: SERVICE_CONTACT_CONSENT,
        MARKETING_CONSENT.purpose: MARKETING_CONSENT,
    }
)
