import { cleanup, render, screen } from "@testing-library/react";
import AboutPage from "@/app/(public)/about/page";
import AccessibilityPage from "@/app/(public)/accessibility/page";
import ComplaintsPage from "@/app/(public)/complaints/page";
import ContactPage from "@/app/(public)/contact/page";
import HowItWorksPage from "@/app/(public)/how-it-works/page";
import MortgagesPage from "@/app/(public)/mortgages/page";
import HomePage from "@/app/(public)/page";
import PrivacyPage from "@/app/(public)/privacy/page";

const pages: Array<[string, () => React.ReactNode]> = [
  ["Start with your mortgage goal", HomePage],
  ["Information for the mortgage decision in front of you", MortgagesPage],
  ["From a general question to a complete application", HowItWorksPage],
  ["About", AboutPage],
  ["Contact", ContactPage],
  ["Privacy", PrivacyPage],
  ["Complaints", ComplaintsPage],
  ["Accessibility", AccessibilityPage],
];

describe("anonymous public pages", () => {
  it.each(pages)(
    "renders %s without an authentication boundary",
    (_label, Page) => {
      render(<>{Page()}</>);
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
      cleanup();
    },
  );

  it("renders careers anonymously from the published-posting boundary", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ items: [], total: 0, limit: 25, offset: 0 }),
      }),
    );
    const { default: CareersPage } = await import(
      "@/app/(public)/careers/page"
    );
    render(<>{await CareersPage()}</>);
    expect(
      screen.getByRole("heading", { level: 1, name: /join keeper financial/i }),
    ).toBeInTheDocument();
    vi.unstubAllGlobals();
  });

  it("renders agents anonymously from the published-profile boundary", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ items: [], total: 0, limit: 25, offset: 0 }),
      }),
    );
    const { default: AgentsPage } = await import("@/app/(public)/agents/page");
    render(<>{await AgentsPage()}</>);
    expect(
      screen.getByRole("heading", {
        level: 1,
        name: /find a keeper financial agent/i,
      }),
    ).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
