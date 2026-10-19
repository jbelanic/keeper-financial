export function AgentPreferenceSection({
  attributedAgentName,
  value,
  onChange,
}: {
  attributedAgentName?: string | null;
  value: string;
  onChange: (next: string) => void;
}) {
  if (attributedAgentName) {
    return (
      <section className="borrower-preference" aria-labelledby="agent-preference">
        <h2 className="visually-hidden" id="agent-preference">
          Your agent
        </h2>
        <p role="status">
          <strong>You are applying with {attributedAgentName}.</strong> They will
          be able to help you finish this application.
        </p>
      </section>
    );
  }

  return (
    <section className="borrower-preference" aria-labelledby="agent-preference">
      <h2 className="visually-hidden" id="agent-preference">
        Your agent
      </h2>
      <p>
        <label htmlFor="preferred-agent-name">
          Are you working with an agent? (optional)
        </label>
      </p>
      <p>
        <input
          id="preferred-agent-name"
          name="preferred_agent_name"
          type="text"
          maxLength={120}
          autoComplete="off"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-describedby="preferred-agent-name-hint"
        />
      </p>
      <p id="preferred-agent-name-hint" className="field-hint">
        Enter their name if you know it. This does not assign them to your file —
        our team confirms the right agent when your application is reviewed.
      </p>
    </section>
  );
}
