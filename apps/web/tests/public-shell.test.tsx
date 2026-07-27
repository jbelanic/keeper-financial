import { render, screen, within } from "@testing-library/react";
import { PublicShell } from "@/lib/shells";
import { publicNavigation } from "@/lib/public-content";
import { siteConfig } from "@/lib/site-config";

describe("public shell", () => {
  it("provides every approved navigation destination and a keyboard-native mobile menu", () => {
    render(
      <PublicShell>
        <p>Page content</p>
      </PublicShell>,
    );

    const primary = screen.getByRole("navigation", { name: "Primary" });
    for (const item of publicNavigation) {
      expect(
        within(primary).getByRole("link", { name: item.label }),
      ).toHaveAttribute("href", item.href);
    }
    expect(
      within(primary).getByRole("link", { name: "Get started" }),
    ).toHaveAttribute("href", "/apply");

    const menuSummary = screen.getByText("Menu");
    expect(menuSummary.tagName).toBe("SUMMARY");
    expect(menuSummary.closest("details")).toBeInTheDocument();
  });

  it("renders exact controlled public identity and real contact actions", () => {
    render(
      <PublicShell>
        <p>Page content</p>
      </PublicShell>,
    );
    expect(
      screen.getByText(new RegExp(siteConfig.regulatoryText)),
    ).toBeInTheDocument();
    expect(screen.getByText(siteConfig.address)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: siteConfig.phoneDisplay }),
    ).toHaveAttribute("href", siteConfig.phoneHref);
    expect(
      screen.getByRole("link", { name: siteConfig.email }),
    ).toHaveAttribute("href", siteConfig.emailHref);
  });
});
