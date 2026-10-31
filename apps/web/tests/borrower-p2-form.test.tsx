import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { DocumentUpload } from "@/app/(borrower)/mortgage-application/components/document-upload";
import { formatAmountInput } from "@/lib/number-input";
import { formatRelativeTime } from "@/lib/relative-time";

describe("amount display", () => {
  it("tidies a valid amount on blur and leaves a bad one alone", () => {
    expect(formatAmountInput("650000")).toBe("650,000");
    expect(formatAmountInput("$2 000")).toBe("2,000");
    expect(formatAmountInput("650000.5")).toBe("650,000.5");
    expect(formatAmountInput("about 650k")).toBe("about 650k");
    expect(formatAmountInput("")).toBe("");
  });
});

describe("relative save time", () => {
  const now = Date.UTC(2026, 9, 31, 12, 0, 0);
  it("describes a save in plain words", () => {
    expect(formatRelativeTime(now - 5_000, now)).toBe("just now");
    expect(formatRelativeTime(now - 60_000, now)).toBe("1 minute ago");
    expect(formatRelativeTime(now - 4 * 60_000, now)).toBe("4 minutes ago");
    expect(formatRelativeTime(now - 60 * 60_000, now)).toBe("1 hour ago");
    expect(formatRelativeTime(now - 26 * 60 * 60_000, now)).toBe("1 day ago");
  });
});

describe("drag-and-drop document upload", () => {
  it("accepts a dropped file and names it before uploading", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const { container } = render(
      <DocumentUpload
        applicationId="11111111-1111-4111-8111-111111111111"
        onSettledChange={vi.fn()}
      />,
    );
    await screen.findByText(/No documents uploaded yet/);

    const zone = container.querySelector(".drop-zone")!;
    const dropped = new File(["safe"], "dropped.pdf", {
      type: "application/pdf",
    });
    fireEvent.dragOver(zone);
    expect(zone.className).toContain("is-dragging");
    fireEvent.drop(zone, { dataTransfer: { files: [dropped] } });

    expect(zone.className).not.toContain("is-dragging");
    expect(screen.getByText(/Selected: dropped\.pdf/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Upload document" }),
    ).toBeEnabled();
  });
});
