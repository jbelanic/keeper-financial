import { render, screen } from "@testing-library/react";
import ApplyPage, { ApplyPaths } from "@/app/(public)/apply/page";
import { safeAgentAttribution } from "@/lib/lead-attribution";
import { getPublicSiteConfig } from "@/lib/site-config";

describe("apply paths and attribution", () => {
  it("renders the public route without authentication and drops unsafe attribution", async () => {
    render(
      await ApplyPage({
        searchParams: Promise.resolve({
          agent: "agent?email=private@example.com",
        }),
      }),
    );

    expect(
      screen.getByRole("heading", {
        name: "Choose how you’d like to begin",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: /Continue to the mortgage application/i,
      }),
    ).not.toHaveAttribute("href", expect.stringContaining("agent="));
  });

  it.each([
    ["published-agent", "published-agent"],
    ["a", "a"],
    ["UPPERCASE", undefined],
    ["agent/path", undefined],
    ["agent?email=private@example.com", undefined],
    ["a".repeat(101), undefined],
    [["agent-one", "agent-two"], undefined],
  ])("normalizes query attribution %s safely", (value, expected) => {
    expect(safeAgentAttribution(value)).toBe(expected);
  });

  it("renders balanced minimal-contact and Keeper-native application paths", () => {
    const config = getPublicSiteConfig({});
    render(<ApplyPaths agentSlug="published-agent" config={config} />);

    expect(
      screen.getByRole("heading", { name: "Ask a general question" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Continue to the mortgage application",
      }),
    ).toBeInTheDocument();
    const mortgageLink = screen.getByRole("link", {
      name: /Continue to the mortgage application/i,
    });
    expect(mortgageLink).toHaveAttribute(
      "href",
      "https://apply.keeperfinancial.ca/?agent=published-agent",
    );
    expect(document.body.textContent).toContain("same-browser");
    expect(
      screen.getAllByText(/Do not (submit|include)/i).length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("shows book-a-call only for an accepted owner HTTPS URL", () => {
    const unavailable = getPublicSiteConfig({
      NEXT_PUBLIC_BOOKING_URL: "javascript:alert(1)",
    });
    const available = getPublicSiteConfig({
      NEXT_PUBLIC_BOOKING_URL: "https://booking.keeper.example/call",
    });
    const { rerender } = render(<ApplyPaths config={unavailable} />);
    expect(
      screen.queryByRole("link", { name: /Book a call/i }),
    ).not.toBeInTheDocument();

    rerender(<ApplyPaths config={available} />);
    expect(screen.getByRole("link", { name: /Book a call/i })).toHaveAttribute(
      "href",
      "https://booking.keeper.example/call",
    );
  });
});
