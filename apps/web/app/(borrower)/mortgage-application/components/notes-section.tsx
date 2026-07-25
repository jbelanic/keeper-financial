import { FormField } from "@keeper/ui";

export function NotesSection({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend>Additional notes</legend>
      <p className="notice">
        Optional. Do not enter passwords, authentication secrets, or unrelated
        third-party personal information.
      </p>
      <FormField
        id="additional-notes"
        label="Additional application notes (optional)"
        hint={`${value.length.toLocaleString()} of 5,000 characters`}
      >
        <textarea
          id="additional-notes"
          maxLength={5000}
          value={value}
          onChange={(event) => onChange(event.currentTarget.value)}
        />
      </FormField>
    </fieldset>
  );
}
