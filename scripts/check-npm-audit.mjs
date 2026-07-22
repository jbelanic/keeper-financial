import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const ADVISORY_URL = "https://github.com/advisories/GHSA-52cp-r559-cp3m";
const REDOCLY_NODE = "node_modules/@redocly/openapi-core";
const YAML_NODE = `${REDOCLY_NODE}/node_modules/js-yaml`;

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
if (names.join(",") !== "@redocly/openapi-core,js-yaml") {
  fail(`unexpected vulnerable packages: ${names.join(", ")}`);
}

const redocly = vulnerabilities["@redocly/openapi-core"];
const yaml = vulnerabilities["js-yaml"];
if (
  redocly.isDirect !== false ||
  redocly.severity !== "high" ||
  redocly.range !== "<=0.0.0-snapshot.1782825774 || 1.34.8 - 1.34.17" ||
  JSON.stringify(redocly.via) !== JSON.stringify(["js-yaml"]) ||
  JSON.stringify(redocly.effects) !== JSON.stringify([]) ||
  JSON.stringify(redocly.nodes) !== JSON.stringify([REDOCLY_NODE])
) {
  fail("the Redocly audit record no longer matches the approved exception");
}
if (
  yaml.isDirect !== false ||
  yaml.severity !== "high" ||
  yaml.range !== "4.0.0 - 4.2.0" ||
  JSON.stringify(yaml.effects) !== JSON.stringify(["@redocly/openapi-core"]) ||
  JSON.stringify(yaml.nodes) !== JSON.stringify([YAML_NODE]) ||
  yaml.via?.length !== 1 ||
  typeof yaml.via[0] !== "object" ||
  yaml.via[0].url !== ADVISORY_URL ||
  yaml.via[0].name !== "js-yaml" ||
  yaml.via[0].range !== ">=4.0.0 <4.3.0" ||
  yaml.via[0].severity !== "high"
) {
  fail("the js-yaml audit record no longer matches the approved exception");
}

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

console.warn(
  `Allowed dev-only ${ADVISORY_URL} for @redocly/openapi-core 1.34.17; all other npm audit findings remain blocking.`,
);
