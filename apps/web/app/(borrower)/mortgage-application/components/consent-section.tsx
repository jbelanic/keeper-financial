export function ConsentSection({
  wording,
  version,
  acknowledged,
  onChange,
}: {
  wording: string;
  version: string;
  acknowledged: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <fieldset>
      <legend>Privacy and credit-use acknowledgement</legend>
      <div className="privacy-disclosure">
        <p>{wording}</p>
        <p>Consent version: {version}</p>
      </div>
      <label className="consent">
        <input
          type="checkbox"
          checked={acknowledged}
          onChange={(event) => onChange(event.currentTarget.checked)}
        />
        <span>
          I acknowledge the privacy and credit-use wording above. This is not a
          signature or marketing consent.
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
