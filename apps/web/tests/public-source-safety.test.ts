import { existsSync, readFileSync, readdirSync } from "node:fs";
import { extname, join } from "node:path";

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? sourceFiles(path) : [path];
  });
}

describe("public source safety and reflow guardrails", () => {
  it("does not leak mockup-only facts or people into production source", () => {
    const source = sourceFiles(join(process.cwd(), "app"))
      .filter((path) => [".ts", ".tsx", ".css"].includes(extname(path)))
      .map((path) => readFileSync(path, "utf8"))
      .join("\n");

    for (const forbidden of [
      "#13372",
      "Sarah Thompson",
      "Michael B.",
      "NMLS",
      "$1.48M",
      "4.49%",
      "60+ lenders",
      "5-star rated",
    ]) {
      expect(source.toLowerCase()).not.toContain(forbidden.toLowerCase());
    }
  });

  it("contains explicit narrow-screen and page-overflow protections", () => {
    const css = readFileSync(join(process.cwd(), "app/globals.css"), "utf8");
    expect(css).toContain("overflow-x: clip");
    expect(css).toContain("@media (max-width: 36rem)");
    expect(css).toContain("grid-template-columns: minmax(0, 1fr)");
  });

  it("centers public feature containers without viewport-derived offsets", () => {
    const css = readFileSync(join(process.cwd(), "app/globals.css"), "utf8");
    const hero = css.split(".page-hero-with-image .page-hero-grid", 2)[1];

    expect(hero).not.toContain("calc((100vw - var(--content-max)) / 2)");
    expect(css).not.toContain("margin-left: max(0px");
    expect(css).toContain(
      ".page-hero-media img {\n  object-position: 58% center;",
    );
    expect(css).toContain("aspect-ratio: 6 / 5");
  });

  it("keeps public image assets outside proxy processing", () => {
    const proxy = readFileSync(join(process.cwd(), "proxy.ts"), "utf8");

    expect(proxy).toContain("_next/image|images/");
  });

  it("does not stream a global loading shell for hard navigations", () => {
    expect(existsSync(join(process.cwd(), "app/loading.tsx"))).toBe(false);
    expect(existsSync(join(process.cwd(), "app/(public)/loading.tsx"))).toBe(
      false,
    );
    const packageJson = readFileSync(
      join(process.cwd(), "package.json"),
      "utf8",
    );
    expect(packageJson).toContain('"dev": "next dev --webpack"');
  });

  it("keeps the application section outline in normal document flow", () => {
    const css = readFileSync(join(process.cwd(), "app/globals.css"), "utf8");
    const progressRule = css.match(/\.progress-nav \{([^}]*)\}/)?.[1] ?? "";

    expect(progressRule).not.toContain("position: sticky");
    expect(progressRule).not.toContain("top:");
    expect(progressRule).not.toContain("z-index:");
  });
});
