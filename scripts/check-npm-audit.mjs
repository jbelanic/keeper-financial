import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

/**
 * npm audit gate.
 *
 * The repository carries a single dated, dev-only exception. It is exact: the
 * flagged package set, every resolved version, every severity and the advisory
 * itself must match the recorded exception, and every flagged package must be a
 * dev dependency in the lockfile. Any new finding, version drift, severity
 * change or additional advisory fails the gate so it is reviewed instead of
 * being absorbed.
 */

// GHSA-g3hv-75wg-m249 - "minimatch has potential denial of service via globparts
// amplification", fixed in 11.0.1. It is reached only through the lint and
// contracts toolchain: eslint (with @eslint/config-array and @eslint/eslintrc),
// typescript-eslint, the eslint plugins, @redocly/openapi-core and
// openapi-typescript all resolve minimatch ^3.x/^5.x, and the current release of
// @eslint/eslintrc (3.3.7) still declares minimatch ^3.1.5. No in-range upgrade
// clears it - `npm audit fix` proposes no package change at all - and forcing
// minimatch 11 through `overrides` would violate the ^3.1.5 ranges those tools
// actually call. Every flagged package is a devDependency and none ships in the
// web or api runtime image.
//
// Exit criteria: remove this exception once the consumers declare ranges that
// resolve minimatch >=11.0.1 (the eslint 10 era toolchain, an @eslint/eslintrc
// release with a modernised dependency, a newer @redocly/openapi-core), then
// empty `packages`, delete this block and let the gate run at zero findings.
const DEV_ONLY_EXCEPTION = {
  asOf: "2026-10-31",
  advisories: ["GHSA-g3hv-75wg-m249"],
  packages: {
    "@eslint-community/eslint-utils": { version: "4.10.1", severity: "moderate" },
    "@eslint/config-array": { version: "0.21.2", severity: "moderate" },
    "@eslint/eslintrc": { version: "3.3.6", severity: "moderate" },
    "@next/eslint-plugin-next": { version: "16.4.3", severity: "moderate" },
    "@redocly/openapi-core": { version: "1.34.22", severity: "moderate" },
    "@typescript-eslint/eslint-plugin": { version: "8.72.0", severity: "moderate" },
    "@typescript-eslint/parser": { version: "8.72.0", severity: "moderate" },
    "@typescript-eslint/type-utils": { version: "8.72.0", severity: "moderate" },
    "@typescript-eslint/typescript-estree": { version: "8.72.0", severity: "moderate" },
    "@typescript-eslint/utils": { version: "8.72.0", severity: "moderate" },
    eslint: { version: "9.39.4", severity: "moderate" },
    "eslint-config-next": { version: "16.4.3", severity: "moderate" },
    "eslint-import-resolver-typescript": { version: "3.10.1", severity: "moderate" },
    "eslint-plugin-import": { version: "2.32.0", severity: "moderate" },
    "eslint-plugin-jsx-a11y": { version: "6.10.2", severity: "moderate" },
    "eslint-plugin-react": { version: "7.37.5", severity: "moderate" },
    "eslint-plugin-react-hooks": { version: "7.1.1", severity: "moderate" },
    minimatch: { version: "3.1.5", severity: "moderate" },
    "openapi-typescript": { version: "7.8.0", severity: "moderate" },
    "typescript-eslint": { version: "8.72.0", severity: "moderate" },
  },
};

function fail(message) {
  console.error(`npm audit check failed: ${message}`);
  process.exit(1);
}

const audit = spawnSync("npm", ["audit", "--json"], {
  encoding: "utf8",
  shell: process.platform === "win32",
});
if (audit.error) fail(`could not execute npm audit: ${audit.error.message}`);
if (![0, 1].includes(audit.status)) {
  fail(`npm audit exited unexpectedly with status ${audit.status}`);
}

let report;
try {
  report = JSON.parse(audit.stdout);
} catch {
  fail("npm audit did not return valid JSON");
}

const vulnerabilities = report.vulnerabilities ?? {};
const names = Object.keys(vulnerabilities).sort();
if (names.length === 0) {
  console.log("npm audit found no vulnerabilities");
  process.exit(0);
}

// --- The flagged set must match the exception exactly ---------------------
const expected = Object.keys(DEV_ONLY_EXCEPTION.packages).sort();
const unexpected = names.filter((name) => !expected.includes(name));
const missing = expected.filter((name) => !names.includes(name));
if (unexpected.length || missing.length) {
  fail(
    [
      unexpected.length ? `unexpected vulnerable packages: ${unexpected.join(", ")}` : null,
      missing.length ? `findings no longer reported: ${missing.join(", ")}` : null,
    ]
      .filter(Boolean)
      .join("; ") + ` (exception recorded ${DEV_ONLY_EXCEPTION.asOf})`,
  );
}

// --- Severity must not move ----------------------------------------------
for (const name of names) {
  const found = vulnerabilities[name];
  const approved = DEV_ONLY_EXCEPTION.packages[name];
  if (found.severity !== approved.severity) {
    fail(
      `severity changed for ${name}: ${approved.severity} approved, ${found.severity} reported`,
    );
  }
}

// --- Only the recorded advisory may be the root cause ---------------------
// Every other `via` entry must be another flagged package, i.e. a dependency
// path inside this set, so a genuinely new advisory cannot ride along.
const advisories = [];
for (const name of names) {
  for (const via of vulnerabilities[name].via ?? []) {
    if (typeof via === "string") {
      if (!names.includes(via)) {
        fail(`${name} is flagged through ${via}, which is not part of the approved set`);
      }
      continue;
    }
    advisories.push({
      package: name,
      url: String(via.url ?? via.source ?? ""),
      title: String(via.title ?? ""),
      severity: String(via.severity ?? ""),
    });
  }
}
const unapproved = advisories.filter(
  (advisory) =>
    !DEV_ONLY_EXCEPTION.advisories.some((id) => advisory.url.includes(id)),
);
if (unapproved.length) {
  fail(
    `unapproved advisories: ${[
      ...new Set(unapproved.map((advisory) => advisory.title || advisory.url)),
    ].join("; ")}`,
  );
}
// If the advisory disappears the findings are no longer the recorded ones, so
// the exception has to be re-reviewed rather than silently reused.
if (!advisories.length) {
  fail("no advisory source is reported, so the dev-only exception no longer applies");
}
if (!advisories.some((advisory) => advisory.severity === "moderate")) {
  fail("the recorded advisory is no longer reported as moderate");
}

// --- Every flagged package must still be a dev-only, unchanged resolution --
let lock;
try {
  lock = JSON.parse(
    readFileSync(new URL("../package-lock.json", import.meta.url), "utf8"),
  );
} catch {
  fail("package-lock.json could not be read as JSON");
}
for (const [name, approved] of Object.entries(DEV_ONLY_EXCEPTION.packages)) {
  const node = lock.packages?.[`node_modules/${name}`];
  if (!node) fail(`${name} is not resolved in package-lock.json`);
  if (node.dev !== true) {
    fail(`${name} is flagged but is not a dev dependency in package-lock.json`);
  }
  if (node.version !== approved.version) {
    fail(
      `the dev-only lockfile shape changed for ${name}: ${approved.version} approved, ${node.version} installed`,
    );
  }
}

console.warn(
  `Allowed dev-only advisory ${DEV_ONLY_EXCEPTION.advisories.join(", ")} across ` +
    `${names.length} lint/contracts packages, all dev-only and resolved to the ` +
    `recorded versions (exception recorded ${DEV_ONLY_EXCEPTION.asOf}). All other ` +
    `npm audit findings remain blocking.`,
);
