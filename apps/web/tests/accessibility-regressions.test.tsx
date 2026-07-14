import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, within } from "@testing-library/react";
import PublicLayout from "@/app/(public)/layout";
import NotFound from "@/app/not-found";

function token(css: string, name: string): string {
  const value = css.match(new RegExp(`--${name}:\\s*(#[0-9a-f]{6})`, "i"))?.[1];
  if (!value) throw new Error(`Missing ${name} color token`);
  return value;
}

function relativeLuminance(hex: string): number {
  const channels = hex
    .slice(1)
    .match(/.{2}/g)
    ?.map((channel) => Number.parseInt(channel, 16) / 255)
    .map((channel) =>
      channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
    );
  if (!channels) throw new Error(`Invalid hex color: ${hex}`);
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrast(first: string, second: string): number {
  const luminances = [relativeLuminance(first), relativeLuminance(second)].sort(
    (a, b) => b - a,
  );
  return (luminances[0] + 0.05) / (luminances[1] + 0.05);
}

describe("accessibility regressions", () => {
  it("keeps white button and navigation text AA-compliant across accent states", () => {
    const css = readFileSync(
      join(process.cwd(), "../../packages/ui/src/tokens.css"),
      "utf8",
    );
    const accent = token(css, "color-accent");
    const hoverAccent = token(css, "color-accent-strong");
    const focus = token(css, "color-focus");

    expect(contrast("#ffffff", accent)).toBeGreaterThanOrEqual(4.5);
    expect(contrast("#ffffff", hoverAccent)).toBeGreaterThanOrEqual(
      contrast("#ffffff", accent),
    );
    expect(contrast("#fffefb", focus)).toBeGreaterThanOrEqual(3);
  });

  it("gives the global fallback exactly one skip-link target and main landmark", () => {
    const { container } = render(<NotFound />);
    const main = within(container).getByRole("main", {
      name: "Page not found",
    });

    expect(within(container).getAllByRole("main")).toHaveLength(1);
    expect(main).toHaveAttribute("id", "main-content");
  });

  it("keeps exactly one main landmark in normal public routes", () => {
    const { container } = render(
      <PublicLayout>
        <p>Page content</p>
      </PublicLayout>,
    );
    const main = within(container).getByRole("main");

    expect(within(container).getAllByRole("main")).toHaveLength(1);
    expect(main).toHaveAttribute("id", "main-content");
  });
});
