import { fireEvent, render, screen } from "@testing-library/react";
import { ApplyPaths } from "@/app/(public)/apply/apply-paths";
import ApplyPage from "@/app/(public)/apply/page";
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
        name: "Before you apply, understand your options.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: /Start Your Application/i,
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

  it("renders the readiness request and the secure application as separate paths", () => {
    const config = getPublicSiteConfig({});
    render(<ApplyPaths agentReference="published-agent" config={config} />);

    expect(
      screen.getByRole("heading", {
        name: "Request your mortgage readiness conversation",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Ready to apply now?" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Start Your Application/i }),
    ).toHaveAttribute(
      "href",
      "https://apply.keeperfinancial.ca/?agent=published-agent",
    );
    expect(document.body.textContent).toContain("this browser");
    expect(
      screen.getAllByText(/don.t (send|use)/i).length,
    ).toBeGreaterThanOrEqual(2);
  });

  it("fills the mortgage goal from a readiness card without leaving the page", () => {
    const config = getPublicSiteConfig({});
    render(<ApplyPaths config={config} />);

    const goals = screen.getAllByRole("radio");
    expect(goals).toHaveLength(6);
    expect(screen.getByLabelText("Mortgage goal")).toHaveValue("");

    fireEvent.click(screen.getByLabelText("Refinancing"));
    expect(screen.getByLabelText("Mortgage goal")).toHaveValue("refinance");
    expect(screen.getByLabelText("Refinancing")).toBeChecked();

    fireEvent.click(screen.getByLabelText("First-time buyer"));
    expect(screen.getByLabelText("Mortgage goal")).toHaveValue("purchase");
    expect(screen.getByLabelText("Refinancing")).not.toBeChecked();

    fireEvent.click(screen.getByLabelText("Not sure yet"));
    expect(screen.getByLabelText("Mortgage goal")).toHaveValue("other");

    // Choosing a goal fills a field; it never submits the request.
    expect(
      screen.getByRole("button", { name: /Send contact request/i }),
    ).toBeEnabled();
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
