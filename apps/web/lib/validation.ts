/**
 * Client-side format checks that mirror the API's own rules.
 *
 * These exist to catch a mistake before a network round trip, not to replace the
 * server: every rule below is copied from `keeper_api.schemas.borrower_payload`
 * so the two cannot disagree about what "valid" means. The server stays
 * authoritative and its message is what gets shown if a value slips through.
 */

export const EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

export const POSTAL_CODE_PATTERN = /^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$/;

export const SIN_LENGTH = 9;

export const EMAIL_HINT = "For example name@example.com.";
export const POSTAL_CODE_HINT = "Canadian format, for example N6H 4T6.";
export const SIN_HINT =
  "Enter the nine digits. The number is checksummed, so a mistyped digit is caught here. It is encrypted and never shown again.";

export function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim());
}

/** Upper-cases and single-spaces a Canadian postal code, as the API stores it. */
export function normalizePostalCode(value: string): string {
  return value.replace(/\s+/g, "").toUpperCase();
}

export function isValidPostalCode(value: string): boolean {
  return POSTAL_CODE_PATTERN.test(value.trim());
}

/**
 * The SIN checksum (Luhn) the API enforces.
 *
 * A nine-digit number that fails here is always rejected on save, so catching it
 * in the form turns a round trip and a server error into an immediate, specific
 * message.
 */
export function passesSinChecksum(value: string): boolean {
  const digits = value.replace(/\D/g, "");
  if (digits.length !== SIN_LENGTH) return false;
  let total = 0;
  for (let index = 0; index < digits.length; index += 1) {
    let digit = Number(digits[digits.length - 1 - index]);
    if (index % 2 === 1) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    total += digit;
  }
  return total % 10 === 0;
}
