import { cleanup, render, screen } from "@testing-library/react";
import AboutPage from "@/app/(public)/about/page";
import AccessibilityPage from "@/app/(public)/accessibility/page";
import AgentsPage from "@/app/(public)/agents/page";
import ApplyPage from "@/app/(public)/apply/page";
import CareersPage from "@/app/(public)/careers/page";
import ComplaintsPage from "@/app/(public)/complaints/page";
import ContactPage from "@/app/(public)/contact/page";
import HowItWorksPage from "@/app/(public)/how-it-works/page";
import MortgagesPage from "@/app/(public)/mortgages/page";
import HomePage from "@/app/(public)/page";
import PrivacyPage from "@/app/(public)/privacy/page";

const pages: Array<[string, () => React.ReactNode]> = [
  ["Ontario mortgage guidance", HomePage],
  ["Mortgage services", MortgagesPage],
  ["How it works", HowItWorksPage],
  ["About", AboutPage],
  ["Contact", ContactPage],
  ["Get started", ApplyPage],
  ["Our agents", AgentsPage],
  ["Join Keeper Financial", CareersPage],
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
});
