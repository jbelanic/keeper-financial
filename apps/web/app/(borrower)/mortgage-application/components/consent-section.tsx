export const DRAFT_CONSENT_VERSION =
  "synthetic-local-borrower-consent-2026-07-25-draft";

export function ConsentSection({
  acknowledged,
  onChange,
}: {
  acknowledged: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <fieldset>
      <legend>Privacy and credit-use acknowledgement</legend>
      <div className="privacy-disclosure">
        <p>
          <strong>Synthetic draft wording — not approved for real use.</strong>
        </p>
        <p>
          For local workflow testing only, I acknowledge that Keeper Financial
          would use the named borrowers’ application information to assess this
          mortgage request and help seek an appropriate mortgage product. If I
          provide co-borrower information, I confirm I have authority to do so.
        </p>
        <p>Draft mechanism version: {DRAFT_CONSENT_VERSION}</p>
      </div>
      <label className="consent">
        <input
          type="checkbox"
          checked={acknowledged}
          onChange={(event) => onChange(event.currentTarget.checked)}
        />
        <span>
          I acknowledge the synthetic draft privacy and credit-use wording
          above. This is not a signature or marketing consent.
        </span>
      </label>
      {!acknowledged ? (
        <p className="field-error" role="status">
          Acknowledgement would be required before final submission.
        </p>
      ) : null}
    </fieldset>
  );
}
