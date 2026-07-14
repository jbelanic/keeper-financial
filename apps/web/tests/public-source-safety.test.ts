import { readFileSync, readdirSync } from "node:fs";
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
});
