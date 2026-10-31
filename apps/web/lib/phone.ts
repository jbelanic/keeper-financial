/**
 * North American phone-number display and input checks.
 *
 * Storage is E.164 (`+15195550123`); people type `5195550123`,
 * `519-555-0123` or `(519) 555 0123`. Everything the interface shows uses the
 * North American display form `(519) 123-4567`.
 */

const NANP_DIGITS = 10;
const E164_MIN_DIGITS = 8;
const E164_MAX_DIGITS = 15;
const ALLOWED_CHARACTERS = /^\+?[0-9 ().-]+$/;

export const PHONE_EXAMPLE = "(519) 123-4567";

export const PHONE_INPUT_ERROR = `Enter a 10-digit phone number, for example ${PHONE_EXAMPLE}.`;

export const PHONE_INPUT_ERROR_INTERNATIONAL = `Enter a 10-digit phone number, for example ${PHONE_EXAMPLE}. For a number outside Canada or the United States, include the + country code.`;

/** The bare 10-digit national number, or null when the value is not NANP. */
export function nanpNationalNumber(
  value: string | null | undefined,
): string | null {
  if (!value) return null;
  const cleaned = value.trim();
  if (!cleaned || !ALLOWED_CHARACTERS.test(cleaned)) return null;
  let digits = cleaned.replace(/\D/g, "");
  if (digits.length === NANP_DIGITS + 1 && digits.startsWith("1")) {
    digits = digits.slice(1);
  }
  return digits.length === NANP_DIGITS ? digits : null;
}

/** Render a stored phone number as `(519) 123-4567`; other values pass through. */
export function formatPhoneDisplay(value: string | null | undefined): string {
  if (!value) return "";
  const national = nanpNationalNumber(value);
  if (!national) return value;
  return `(${national.slice(0, 3)}) ${national.slice(3, 6)}-${national.slice(6)}`;
}

/** The `tel:` target for a stored or typed phone number. */
export function phoneTelHref(value: string | null | undefined): string {
  if (!value) return "";
  const national = nanpNationalNumber(value);
  if (national) return `tel:+1${national}`;
  const digits = value.replace(/\D/g, "");
  if (!digits) return "";
  return value.trim().startsWith("+") ? `tel:+${digits}` : `tel:${digits}`;
}

/**
 * Whether a typed value is usable as a contact number: a 10-digit North
 * American number, or an explicit international number with 8 to 15 digits.
 */
export function isAcceptablePhoneInput(
  value: string | null | undefined,
): boolean {
  if (!value) return false;
  const cleaned = value.trim();
  if (!cleaned || !ALLOWED_CHARACTERS.test(cleaned)) return false;
  if (nanpNationalNumber(cleaned)) return true;
  if (!cleaned.startsWith("+")) return false;
  const digits = cleaned.replace(/\D/g, "");
  return digits.length >= E164_MIN_DIGITS && digits.length <= E164_MAX_DIGITS;
}

/** The browser `pattern` attribute shared by the phone inputs. */
export const PHONE_INPUT_PATTERN = "\\+?[0-9 \\(\\)\\.\\-]{10,32}";
