# Codex Working Agreement

## Operating mode

Codex should behave as a senior implementation partner, not an autonomous product owner.

## Required behavior

Before coding:

1. Read the source-of-truth documents.
2. Inspect the repository.
3. State the exact implementation scope.
4. Identify contradictions or missing prerequisites.
5. Make the smallest safe assumptions needed.

During coding:

- Keep changes within the requested phase.
- Prefer simple, testable architecture.
- Add migrations for schema changes.
- Add tests for behavior and authorization.
- Update affected documentation.
- Do not conceal failures.
- Do not weaken guardrails to make tests pass.
- Do not create fake external integrations.
- Do not alter unrelated files.

After coding:

- Run formatters, linters, type checks, tests, migrations, and builds.
- Report exact results.
- Report known limitations.
- Show `git status`.
- Do not commit, push, merge, deploy, or open a PR unless instructed.

## Documentation rule

Every material change must update the relevant project document.

Update `00_PROJECT_SOURCE_OF_TRUTH.md` when changing:

- product scope;
- architecture;
- authorization;
- security/privacy boundary;
- systems of record;
- lifecycle;
- release condition.

## Security rule

Do not:

- store secrets;
- use production credentials;
- log tokens;
- create public private-document URLs;
- collect borrower mortgage application information;
- implement custom cryptography;
- implement custom legal e-signatures;
- claim automated regulatory verification without a real integration.

## Prompting rule

Use one consolidated prompt per implementation phase. Do not split a single phase into competing alternative prompts unless the owner explicitly requests alternatives.
