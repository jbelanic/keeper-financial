const AGENT_SLUG = /^[a-z0-9-]{1,100}$/;

export function safeAgentAttribution(
  value: string | string[] | undefined,
): string | undefined {
  return typeof value === "string" && AGENT_SLUG.test(value)
    ? value
    : undefined;
}
