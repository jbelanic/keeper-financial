import { render, screen, within } from "@testing-library/react";
import AdminOverviewPage from "@/app/(admin)/admin/page";
import { getAdminOverview } from "@/lib/admin-overview";

vi.mock("@/lib/admin-overview", () => ({
  getAdminOverview: vi.fn(),
}));

const mockedGetAdminOverview = vi.mocked(getAdminOverview);

describe("admin overview", () => {
  it("replaces the stale foundation panel with current lead, candidate, and borrower summaries", async () => {
    mockedGetAdminOverview.mockResolvedValue({
      leads: {
        total: 6,
        items: [
          {
            id: "00000000-0000-4000-8000-000000000001",
            title: "Synthetic Lead",
            status: "new",
            href: "/admin/leads?status=new",
            detail: "Email contact · renewal",
          },
        ],
      },
      candidates: {
        total: 2,
        items: [
          {
            id: "00000000-0000-4000-8000-000000000002",
            title: "Candidate Applicant",
            status: "under_review",
            href: "/admin/candidates",
            detail: "Mortgage Agent posting",
          },
        ],
      },
      borrowers: {
        total: 3,
        items: [
          {
            id: "00000000-0000-4000-8000-000000000003",
            title: "Borrower application",
            status: "submitted",
            href: "/admin/borrower-applications",
            detail: "Submitted mortgage application",
          },
        ],
      },
    });

    render(await AdminOverviewPage());

    expect(
      screen.queryByRole("heading", { name: /Foundation readiness/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Administration overview/i }),
    ).toBeInTheDocument();

    const leads = screen.getByRole("region", { name: /Top 5 leads/i });
    expect(
      within(leads).getByRole("link", { name: /Synthetic Lead/i }),
    ).toHaveAttribute("href", "/admin/leads?status=new");
    expect(within(leads).getByText("new")).toBeInTheDocument();

    const candidates = screen.getByRole("region", {
      name: /New candidate submissions/i,
    });
    expect(
      within(candidates).getByRole("link", { name: /Candidate Applicant/i }),
    ).toHaveAttribute("href", "/admin/candidates");
    expect(within(candidates).getByText("under review")).toBeInTheDocument();

    const borrowers = screen.getByRole("region", {
      name: /Top 5 borrower applications/i,
    });
    expect(
      within(borrowers).getByRole("link", { name: /Borrower application/i }),
    ).toHaveAttribute("href", "/admin/borrower-applications");
    expect(within(borrowers).getByText("submitted")).toBeInTheDocument();
  });
});
