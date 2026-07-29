export function AgentPreferenceSection({ slug }: { slug: string }) {
  if (!slug) return null;

  return (
    <section className="borrower-preference" aria-labelledby="agent-preference">
      <h2 className="visually-hidden" id="agent-preference">
        Selected agent
      </h2>
      <p>
        <strong>Selected agent:</strong> {slug}
      </p>
    </section>
  );
}
