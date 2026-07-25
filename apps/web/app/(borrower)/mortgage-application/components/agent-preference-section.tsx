export function AgentPreferenceSection({ slug }: { slug: string }) {
  return (
    <section className="borrower-preference" aria-labelledby="agent-preference">
      <h2 id="agent-preference">Agent preference</h2>
      {slug ? (
        <p>
          You arrived with the preference <strong>{slug}</strong>. Keeper
          validates public-agent eligibility on the server. A preference is
          attribution, not authorization or guaranteed assignment.
        </p>
      ) : (
        <p>
          No agent preference was supplied. An administrator can route the
          application after future submission.
        </p>
      )}
    </section>
  );
}
