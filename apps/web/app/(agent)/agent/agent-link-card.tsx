"use client";

import { useEffect, useState } from "react";
import { Button, Card } from "@keeper/ui";
import { agentBrowserRequest } from "@/lib/agent-browser-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;

// The referral link is the agent's own shareable entry point, so it is loaded on
// its own and never behind the assigned-applications queue: a queue failure must
// not hide the link.
export function AgentLinkCard({
  requester = agentBrowserRequest,
}: {
  requester?: Requester;
}) {
  const [applyLink, setApplyLink] = useState<string | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "unavailable">(
    "loading",
  );
  const [linkCopied, setLinkCopied] = useState(false);

  useEffect(() => {
    let active = true;
    requester("/api/v1/agent-referral-link")
      .then(async (response) => {
        if (!active) return;
        if (!response.ok) {
          setState("unavailable");
          return;
        }
        const body = (await response.json()) as { apply_url?: unknown };
        if (typeof body.apply_url !== "string" || !body.apply_url) {
          setState("unavailable");
          return;
        }
        setApplyLink(body.apply_url);
        setState("ready");
      })
      .catch(() => {
        if (active) setState("unavailable");
      });
    return () => {
      active = false;
    };
  }, [requester]);

  async function copyApplyLink() {
    if (!applyLink) return;
    try {
      await navigator.clipboard.writeText(applyLink);
      setLinkCopied(true);
    } catch {
      setLinkCopied(false);
    }
  }

  return (
    <Card aria-labelledby="agent-link-heading">
      <h2 id="agent-link-heading">Your application link</h2>
      {state === "ready" && applyLink ? (
        <>
          <p>
            Share this link with clients. Applications they start from it are
            assigned to you automatically.
          </p>
          <p>
            <code id="agent-apply-link">{applyLink}</code>
          </p>
          <Button type="button" onClick={copyApplyLink}>
            {linkCopied ? "Copied" : "Copy link"}
          </Button>
        </>
      ) : state === "unavailable" ? (
        <p className="muted">
          Your application link could not be loaded. Sign out and sign in again;
          if it still does not appear, contact support.
        </p>
      ) : (
        <p className="muted">Loading your application link…</p>
      )}
    </Card>
  );
}
