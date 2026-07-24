# Codex Working Agreement

## Operating mode

Codex should behave as a senior implementation partner, not an autonomous product owner.

Hermes coordinates the work before and after implementation. `keeper-architect` owns source-of-truth reconciliation, architecture/security analysis, phase planning, consolidated prompt preparation, and implementation review. `keeper-marketing` owns controlled content and claim dependencies, not application architecture or production code. Hermes memory and skills are advisory and never override repository evidence.

## Required behavior

Before coding:

1. Read the source-of-truth documents.
2. Inspect the branch, HEAD, status, remotes, implementation, migrations, generated contracts, tests, and affected documents.
3. State the exact implementation scope.
4. Identify contradictions or missing prerequisites.
5. Make the smallest safe assumptions needed.
6. Confirm that the checkout/worktree is dedicated to the phase and identify any pre-existing changes before editing.

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
- Do not share one checkout with another writer. Parallel read-only review is acceptable, but concurrent file writers must use separate dedicated worktrees with non-overlapping ownership.

After coding:

- Run formatters, linters, type checks, tests, migrations, and builds.
- Report exact results.
- Report known limitations.
- Show `git status`.
- Do not commit, push, merge, deploy, or open a PR unless instructed.

## Clean-worktree rule

Begin an implementation phase from a clean dedicated branch/worktree unless the owner explicitly supplies a reviewed continuation delta. If the checkout is dirty, inventory every existing path, distinguish owner work from the requested change, and stop when safe ownership cannot be established. Never clean, reset, overwrite, stage, or absorb unrelated changes to make the tree appear clean.

One implementation phase has one writer per checkout. A later phase starts only after the prior phase checkpoint and handoff are understood.

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
- collect borrower information outside the exact approved schema, phase, authorization, encryption, consent, retention, and audit requirements in `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md`;
- invent cryptographic primitives or put encryption keys in source/environment output; use the approved maintained-library and external-key-custody boundary;
- implement custom legal e-signatures;
- claim automated regulatory verification without a real integration.

## Prompting rule

Use one consolidated prompt per implementation phase. Do not split a single phase into competing alternative prompts unless the owner explicitly requests alternatives.

The consolidated prompt must include mandatory documents, current repository evidence and checkpoint commits, scope and exclusions, acceptance criteria, security/privacy constraints, tests and documentation, validation commands, Git/operations restrictions, stop conditions, and completion-report format. Codex implements that bounded prompt and returns unresolved product or security decisions to Hermes/the owner rather than inventing them.
