/** Shared option vocabularies for the borrower application form. */

export const provinces = [
  "AB",
  "BC",
  "MB",
  "NB",
  "NL",
  "NS",
  "NT",
  "NU",
  "ON",
  "PE",
  "QC",
  "SK",
  "YT",
] as const;

/**
 * Payment frequencies offered by the select controls.
 *
 * The API stores a plain string (max 20 characters), so an older draft may hold
 * a value that is not in this list. The selects render such a value as its own
 * option rather than silently replacing it with the first entry.
 */
export const paymentFrequencies = [
  ["monthly", "Monthly"],
  ["semi_monthly", "Semi-monthly"],
  ["bi_weekly", "Bi-weekly"],
  ["weekly", "Weekly"],
  ["annual", "Annual"],
] as const;

export function paymentFrequencyLabel(value: string): string {
  return paymentFrequencies.find(([code]) => code === value)?.[1] ?? value;
}
