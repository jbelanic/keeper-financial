import type { Metadata } from "next";
import { Card, StatusBadge } from "@keeper/ui";
import {
  getAdminOverview,
  type AdminOverviewSection,
} from "@/lib/admin-overview";

export const metadata: Metadata = { title: "Brokerage administration" };

const SECTION_CONFIG = [
  {
    key: "leads",
    title: "Top 5 leads",
    description: "Newest contact requests from the public Get Started flow.",
    allHref: "/admin/leads",
    allLabel: "View all leads",
  },
  {
    key: "candidates",
    title: "New candidate submissions",
    description:
      "Current candidate applications awaiting administrator review.",
    allHref: "/admin/candidates",
    allLabel: "View candidate queue",
  },
  {
    key: "borrowers",
    title: "Top 5 borrower applications",
    description: "Newest submitted borrower mortgage applications in review.",
    allHref: "/admin/borrower-applications",
    allLabel: "View borrower review",
  },
] as const;

function statusTone(
  status: string,
): "neutral" | "success" | "warning" | "danger" {
  if (["closed", "completed", "conditionally_selected"].includes(status))
    return "success";
  if (["declined", "withdrawn", "expired"].includes(status)) return "danger";
  if (["new", "submitted", "under_review", "interview"].includes(status))
    return "warning";
  return "neutral";
}

function AdminOverviewCard({
  title,
  description,
  section,
  allHref,
  allLabel,
}: {
  title: string;
  description: string;
  section: AdminOverviewSection;
  allHref: string;
  allLabel: string;
}) {
  return (
    <section aria-label={title} className="admin-overview-section">
      <Card>
        <div className="admin-overview-card-heading">
          <div>
            <h2>{title}</h2>
            <p>{description}</p>
          </div>
          <StatusBadge tone="neutral">{section.total} total</StatusBadge>
        </div>
        {section.items.length ? (
          <ul className="admin-overview-list">
            {section.items.map((item) => (
              <li key={item.id}>
                <div>
                  <a href={item.href}>{item.title}</a>
                  <p>{item.detail}</p>
                </div>
                <StatusBadge tone={statusTone(item.status)}>
                  {item.status.replace(/_/g, " ")}
                </StatusBadge>
              </li>
            ))}
          </ul>
        ) : (
          <p className="admin-overview-empty">
            Nothing currently waiting here.
          </p>
        )}
        <a className="admin-overview-all-link" href={allHref}>
          {allLabel}
        </a>
      </Card>
    </section>
  );
}

export default async function AdminOverviewPage() {
  const overview = await getAdminOverview();
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Brokerage administration</p>
        <h1>Administration overview</h1>
        <p>
          Review current contact leads, candidate submissions, and borrower
          mortgage applications from one controlled landing page.
        </p>
      </header>
      <div className="admin-overview-grid">
        {SECTION_CONFIG.map((section) => (
          <AdminOverviewCard
            key={section.key}
            title={section.title}
            description={section.description}
            section={overview[section.key]}
            allHref={section.allHref}
            allLabel={section.allLabel}
          />
        ))}
      </div>
    </>
  );
}
