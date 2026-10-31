/**
 * Numeric and money entry for the borrower application.
 *
 * A section save used to run `Number(value)` on whatever was typed, so a
 * perfectly normal entry like `650,000` became `NaN`, serialised to `null`, and
 * the served payload simply omitted the field — the section reported "saved"
 * and the applicant only discovered the loss at submission. Parsing is now
 * explicit and every rejected entry produces a message instead of silence.
 */

export type NumberKind = "money" | "integer";

export type ParsedNumber =
  | { state: "empty" }
  | { state: "valid"; value: number }
  | { state: "invalid"; reason: "format" | "precision" };

const THOUSANDS_SEPARATORS = /[$,\s\u00a0\u202f\u2009]/g;
const MONEY_PATTERN = /^(?:\d+(?:\.\d{1,2})?|\.\d{1,2})$/;
const EXCESS_PRECISION = /^\d*\.\d{3,}$/;
const INTEGER_PATTERN = /^\d+$/;

/** Parse a typed amount or whole number, tolerating `$`, commas, and spaces. */
export function parseNumberInput(
  raw: string | null | undefined,
  kind: NumberKind = "money",
): ParsedNumber {
  const cleaned = (raw ?? "").replace(THOUSANDS_SEPARATORS, "").trim();
  if (!cleaned) return { state: "empty" };
  if (kind === "integer") {
    if (!INTEGER_PATTERN.test(cleaned))
      return { state: "invalid", reason: "format" };
    const value = Number(cleaned);
    return Number.isSafeInteger(value)
      ? { state: "valid", value }
      : { state: "invalid", reason: "format" };
  }
  if (EXCESS_PRECISION.test(cleaned))
    return { state: "invalid", reason: "precision" };
  if (!MONEY_PATTERN.test(cleaned))
    return { state: "invalid", reason: "format" };
  const value = Number(cleaned);
  return Number.isFinite(value)
    ? { state: "valid", value }
    : { state: "invalid", reason: "format" };
}

/** The value to send, or `undefined` when nothing was entered. */
export function numberValue(
  raw: string | null | undefined,
  kind: NumberKind = "money",
): number | undefined {
  const parsed = parseNumberInput(raw, kind);
  return parsed.state === "valid" ? parsed.value : undefined;
}

/**
 * Tidy a valid amount for display when the field loses focus: `650000` becomes
 * `650,000` and `$2 000` becomes `2,000`. An entry that could not be parsed is
 * left exactly as typed so the rejection message still refers to it.
 */
export function formatAmountInput(raw: string): string {
  const parsed = parseNumberInput(raw, "money");
  if (parsed.state !== "valid") return raw;
  return parsed.value.toLocaleString("en-CA", { maximumFractionDigits: 2 });
}

/** One sentence explaining why an entry was rejected. */
export function numberIssueMessage(
  label: string,
  kind: NumberKind,
  reason: "format" | "precision",
): string {
  if (reason === "precision") {
    return `${label} can have at most two decimal places.`;
  }
  return kind === "integer"
    ? `${label} must be a whole number, for example 2.`
    : `${label} must be an amount, for example 650000 or 650,000.`;
}

export type NumberCheck = {
  label: string;
  raw: string | null | undefined;
  kind?: NumberKind;
};

/** Every message for the amounts in one section, in the order given. */
export function numberChecks(checks: NumberCheck[]): string[] {
  return checks.flatMap(({ label, raw, kind = "money" }) => {
    const parsed = parseNumberInput(raw, kind);
    return parsed.state === "invalid"
      ? [numberIssueMessage(label, kind, parsed.reason)]
      : [];
  });
}
