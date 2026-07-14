import type { Metadata } from "next";
import { Card, ProgressChecklist, StatusBadge, Timeline } from "@keeper/ui";
export const metadata: Metadata = { title: "Candidate portal" };
export default function Page() {
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Candidate portal</p>
        <h1>Your recruitment journey</h1>
        <p>
          The shell is protected by verified identity, a local candidate role,
          an active user, and allowed lifecycle state.
        </p>
      </header>
      <div className="grid-2">
        <Card>
          <h2>
            Foundation status{" "}
            <StatusBadge tone="warning">Not started</StatusBadge>
          </h2>
          <ProgressChecklist
            items={[
              { label: "Application workflow", complete: false },
              { label: "Selection workflow", complete: false },
              { label: "Onboarding workflow", complete: false },
            ]}
          />
        </Card>
        <Card>
          <h2>Status timeline</h2>
          <Timeline
            items={[
              {
                label: "Account access",
                detail: "Authorization foundation active",
              },
              {
                label: "Next",
                detail: "Candidate workflow arrives in Phase 1C",
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}
