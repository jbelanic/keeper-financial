from typing import Protocol


class EsignAdapter(Protocol):
    """Boundary for a future established e-signature provider."""

    def envelope_status(self, external_envelope_id: str) -> str: ...


class CrmAdapter(Protocol):
    """Boundary for future CRM event delivery; no implementation exists in Phase 0."""

    def publish_event(self, event_name: str, safe_reference: str) -> None: ...
