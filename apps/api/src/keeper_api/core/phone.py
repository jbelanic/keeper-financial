"""North American phone-number parsing and formatting.

The public and internal forms must accept the way people actually type a phone
number — ``5195550123``, ``519-555-0123``, ``(519) 555 0123`` or ``+1 519 555
0123`` — and store one canonical value. Storage is E.164 (``+15195550123``);
presentation is the North American display form ``(519) 555-0123``.

Anything that is not a 10-digit North American number is rejected rather than
stored as free text, because an unusable contact number silently blocks the
follow-up the applicant asked for.
"""

from __future__ import annotations

import re

_NANP_DIGITS = 10
_E164_MIN_DIGITS = 8
_E164_MAX_DIGITS = 15
_ALLOWED_CHARACTERS = re.compile(r"^\+?[0-9 ().-]+$")

NANP_ERROR = "Enter a 10-digit phone number, for example (519) 123-4567."
INTERNATIONAL_ERROR = (
    "Enter a 10-digit phone number, for example (519) 123-4567. "
    "For a number outside Canada or the United States, include the + country code."
)


def _clean(value: str) -> str:
    return value.strip()


def nanp_national_number(value: str | None) -> str | None:
    """Return the bare 10-digit national number, or ``None`` when it is not NANP.

    A leading ``1`` (with or without ``+``) is accepted as the North American
    country code and dropped. Punctuation, spaces and dots are ignored.
    """
    if value is None:
        return None
    cleaned = _clean(value)
    if not cleaned or not _ALLOWED_CHARACTERS.fullmatch(cleaned):
        return None
    digits = re.sub(r"\D", "", cleaned)
    if len(digits) == _NANP_DIGITS + 1 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != _NANP_DIGITS:
        return None
    return digits


def normalize_nanp_phone(value: str | None) -> str | None:
    """Normalise a North American number to E.164 (``+1XXXXXXXXXX``)."""
    if value is None:
        return None
    cleaned = _clean(value)
    if not cleaned:
        return None
    national = nanp_national_number(cleaned)
    if national is None:
        raise ValueError(NANP_ERROR)
    return f"+1{national}"


def normalize_phone(value: str | None, *, allow_international: bool) -> str | None:
    """Normalise a phone number to E.164.

    ``allow_international`` keeps an explicitly international number usable (a
    candidate or contact who lives abroad) while still refusing a bare digit run
    that is not a North American number.
    """
    if value is None:
        return None
    cleaned = _clean(value)
    if not cleaned:
        return None
    national = nanp_national_number(cleaned)
    if national is not None:
        return f"+1{national}"
    if allow_international and cleaned.startswith("+") and _ALLOWED_CHARACTERS.fullmatch(cleaned):
        digits = re.sub(r"\D", "", cleaned)
        if _E164_MIN_DIGITS <= len(digits) <= _E164_MAX_DIGITS:
            return f"+{digits}"
    raise ValueError(INTERNATIONAL_ERROR if allow_international else NANP_ERROR)


def format_phone_display(value: str | None) -> str | None:
    """Render a stored phone number as ``(519) 123-4567``.

    Values that are not a North American number are returned unchanged so a
    historically stored value is never hidden or mangled in the interface.
    """
    if value is None:
        return None
    national = nanp_national_number(value)
    if national is None:
        return value
    return f"({national[:3]}) {national[3:6]}-{national[6:]}"


def phone_tel_href(value: str | None) -> str | None:
    """Build the ``tel:`` target for a stored phone number."""
    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    if not digits:
        return None
    national = nanp_national_number(value)
    if national is None:
        return f"tel:+{digits}" if value.strip().startswith("+") else f"tel:{digits}"
    return f"tel:+1{national}"
