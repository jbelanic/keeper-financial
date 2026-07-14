import type { Metadata } from "next";
import { Card, DataTable, StatusBadge } from "@keeper/ui";
export const metadata: Metadata = { title: "Administration portal" };
export default function Page() {
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Brokerage administration</p>
        <h1>Controlled work starts here.</h1>
        <p>
          This shell requires a verified, active local user with the
          brokerage-admin role. Nonlocal environments also require an MFA
          assurance level of AAL2.
        </p>
      </header>
      <Card>
        <h2>Foundation readiness</h2>
        <DataTable
          caption="Phase 0 administration boundaries"
          headers={["Boundary", "Status"]}
          rows={[
            [
              "Role and lifecycle authorization",
              <StatusBadge key="a" tone="success">
                Implemented
              </StatusBadge>,
            ],
            [
              "Candidate queues",
              <StatusBadge key="b" tone="warning">
                Phase 1D
              </StatusBadge>,
            ],
            [
              "Profile approval",
              <StatusBadge key="c" tone="warning">
                Service foundation
              </StatusBadge>,
            ],
          ]}
        />
      </Card>
    </>
  );
}
