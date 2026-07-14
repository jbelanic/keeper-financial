import { ADMIN_ROUTES, CANDIDATE_ROUTES, PUBLIC_ROUTES } from "@/lib/routes";

describe("route inventory", () => {
  it("keeps all required public routes outside portal inventories", () => {
    expect(PUBLIC_ROUTES).toEqual(
      expect.arrayContaining([
        "/",
        "/apply",
        "/agents/[slug]",
        "/careers/[slug]",
        "/privacy",
        "/complaints",
        "/accessibility",
      ]),
    );
    expect(
      PUBLIC_ROUTES.some(
        (route) => route.startsWith("/candidate") || route.startsWith("/admin"),
      ),
    ).toBe(false);
  });

  it("classifies every protected candidate and admin route", () => {
    expect(CANDIDATE_ROUTES).toHaveLength(4);
    expect(
      CANDIDATE_ROUTES.every((route) => route.startsWith("/candidate")),
    ).toBe(true);
    expect(ADMIN_ROUTES).toHaveLength(5);
    expect(ADMIN_ROUTES.every((route) => route.startsWith("/admin"))).toBe(
      true,
    );
  });
});
