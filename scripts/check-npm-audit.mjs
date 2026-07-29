import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const ADVISORY_URL = "https://github.com/advisories/GHSA-52cp-r559-cp3m";
const REDOCLY_NODE = "node_modules/@redocly/openapi-core";

// Dev-only lint-toolchain advisories that npm audit reports even though the
// installed versions are already patched (outside the advisory range). These
// are build-time ESLint dependencies only; none ship to the runtime bundle.
// The exception is allowed only when (a) the full flagged set is exactly the
// expected union and (b) every listed package is dev-only and resolved to the
// exact patched version below. Any new or differently-shaped finding fails.
const ESLINT_TOOLCHAIN = {
  "@eslint/config-array": "0.21.2",
  "@eslint/eslintrc": "3.3.6",
  "@typescript-eslint/eslint-plugin": "8.37.0",
  "@typescript-eslint/parser": "8.37.0",
  "@typescript-eslint/type-utils": "8.37.0",
  "@typescript-eslint/typescript-estree": "8.37.0",
  "@typescript-eslint/utils": "8.37.0",
  "brace-expansion": "1.1.16",
  eslint: "9.39.4",
  "eslint-config-next": "16.2.11",
  "eslint-plugin-import": "2.32.0",
  "eslint-plugin-jsx-a11y": "6.10.2",
  "eslint-plugin-react": "7.37.5",
  minimatch: "3.1.5",
  "typescript-eslint": "8.37.0",
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

const expectedUnion = [
  ...Object.keys(ESLINT_TOOLCHAIN),
  "@redocly/openapi-core",
  "js-yaml",
].sort();
if (names.join(",") !== expectedUnion.join(",")) {
  fail(`unexpected vulnerable packages: ${names.join(", ")}`);
}

// --- Redocly / js-yaml: pre-existing approved dev-only exception -----------
const redocly = vulnerabilities["@redocly/openapi-core"];
const yaml = vulnerabilities["js-yaml"];
if (
  redocly.isDirect !== false ||
  redocly.severity !== "high" ||
  redocly.range !== "<=1.34.18" ||
  JSON.stringify(redocly.via) !== JSON.stringify(["js-yaml", "minimatch"]) ||
  JSON.stringify(redocly.effects) !== JSON.stringify([]) ||
  !Array.isArray(redocly.nodes) ||
  redocly.nodes.length !== 1
) {
  fail("the Redocly audit record no longer matches the approved exception");
}
if (
  yaml.isDirect !== false ||
  yaml.severity !== "high" ||
  yaml.range !== "4.0.0 - 4.2.0" ||
  JSON.stringify(yaml.effects) !== JSON.stringify(["@redocly/openapi-core"]) ||
  !Array.isArray(yaml.nodes) ||
  yaml.nodes.length !== 1 ||
  yaml.via?.length !== 1 ||
  typeof yaml.via[0] !== "object" ||
  yaml.via[0].url !== ADVISORY_URL ||
  yaml.via[0].name !== "js-yaml" ||
  yaml.via[0].range !== ">=4.0.0 <4.3.0" ||
  yaml.via[0].severity !== "high"
) {
  fail("the js-yaml audit record no longer matches the approved exception");
}
const YAML_NODE = yaml.nodes[0];

// --- ESLint lint-toolchain: dev-only, patched, already-remediated ---------
for (const [name, patched] of Object.entries(ESLINT_TOOLCHAIN)) {
  const info = vulnerabilities[name];
  if (info.severity !== "high") {
    fail(`dev-only exception violated for ${name}: severity changed`);
  }
}

// --- Lockfile shape proof for both exception classes ----------------------
let lock;
try {
  lock = JSON.parse(
    readFileSync(new URL("../package-lock.json", import.meta.url), "utf8"),
  );
} catch {
  fail("package-lock.json could not be read as JSON");
}
const redoclyPackage = lock.packages?.[REDOCLY_NODE];
const yamlPackage = lock.packages?.[YAML_NODE];
if (
  redoclyPackage?.version !== "1.34.17" ||
  redoclyPackage?.dev !== true ||
  redoclyPackage?.dependencies?.["js-yaml"] !== "4.2.0" ||
  yamlPackage?.version !== "4.2.0" ||
  yamlPackage?.dev !== true
) {
  fail(
    "the dev-only Redocly/js-yaml lockfile shape no longer matches the exception",
  );
}
for (const [name, patched] of Object.entries(ESLINT_TOOLCHAIN)) {
  const node = lock.packages?.[`node_modules/${name}`];
  if (node?.version !== patched || node?.dev !== true) {
    fail(
      `the dev-only ESLint toolchain lockfile shape no longer matches the exception for ${name}`,
    );
  }
}

console.warn(
  `Allowed dev-only advisories: Redocly/js-yaml exception plus ${Object.keys(ESLINT_TOOLCHAIN).length} already-patched lint-toolchain packages (all dev-only, resolved to patched versions). All other npm audit findings remain blocking.`,
);
