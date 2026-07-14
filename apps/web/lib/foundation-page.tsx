import { Breadcrumbs, Card, EmptyState, StatusBadge } from "@keeper/ui";

export function FoundationPage({
  title,
  description,
  area = "public",
}: {
  title: string;
  description: string;
  area?: "public" | "candidate" | "admin";
}) {
  return (
    <>
      <header className="foundation-header">
        <Breadcrumbs
          items={
            area === "public"
              ? [{ label: "Home", href: "/" }, { label: title }]
              : [
                  {
                    label: `${area === "admin" ? "Administration" : "Candidate"} portal`,
                    href: `/${area}`,
                  },
                  { label: title },
                ]
          }
        />
        <p className="eyebrow">Phase 0 foundation</p>
        <h1>{title}</h1>
        <p>{description}</p>
      </header>
      <Card>
        <StatusBadge tone="warning">Foundation content</StatusBadge>
        <EmptyState title="Workflow ready for the next delivery phase">
          This route, navigation, responsive shell, and authorization boundary
          are implemented. Final content and workflow behavior will be added
          only in its scheduled phase.
        </EmptyState>
      </Card>
    </>
  );
}
