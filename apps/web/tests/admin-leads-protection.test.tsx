import { render, screen } from "@testing-library/react";

const { requirePortalAccess } = vi.hoisted(() => ({
  requirePortalAccess: vi.fn().mockResolvedValue(undefined),
}));
vi.mock("@/lib/require-portal-access", () => ({ requirePortalAccess }));

import AdminLayout from "@/app/(admin)/layout";

describe("admin lead route protection", () => {
  it("keeps the lead route inside the server-protected admin layout", async () => {
    render(
      await AdminLayout({
        children: <p>Protected lead queue</p>,
      }),
    );
    expect(requirePortalAccess).toHaveBeenCalledWith("admin");
    expect(screen.getByRole("link", { name: "Leads" })).toHaveAttribute(
      "href",
      "/admin/leads",
    );
    expect(screen.getAllByRole("main")).toHaveLength(1);
  });
});
