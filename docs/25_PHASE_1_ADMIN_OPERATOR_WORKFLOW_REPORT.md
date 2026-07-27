# Phase 1 Administrator Operator-Workflow Implementation Report

- **Date:** 2026-07-19
- **Branch:** `feat/admin-workflow-operator-ux`
- **Starting checkpoint:** `3331519de482c2bd062b7b7e10e067f06c42f9a3`
- **Candidate migration head:** `20260719_0008`
- **Status at report generation:** owner-accepted Phase 1 source implementation in an uncommitted and unmerged worktree; independent pre-commit findings remediated and full deterministic re-verification complete. This report does not grant production, pilot, deployment, or activation authority.

## 2026-07-19 post-verification owner decision

The owner explicitly accepted the Phase 1 source implementation, including this administrator/operator refinement. At acceptance reconciliation, Git still showed branch `feat/admin-workflow-operator-ux` at starting checkpoint `3331519de482c2bd062b7b7e10e067f06c42f9a3` with the accepted implementation uncommitted and unmerged.

This acceptance is confined to source. It does not authorize commit, push, pull request, merge, history rewriting, deployment, shared-database migration, production or controlled-pilot operation, final candidate activation, candidate-to-agent transition, agent-role grant, credential or external-service changes, destructive operations, or legal/privacy/regulatory/claims/accessibility approval.

Phase 1F production and controlled-pilot readiness planning is the next gate. Phase 1F implementation remains prohibited until its plan, evidence requirements, owner decisions, scope, and acceptance criteria are approved.

## 2026-07-19 Git-publication update

After separate owner authorization, the accepted refinement was committed at `17e1b43` and integrated into the publication candidate with local `main` content commit `07895c2` without history rewriting. Validation, pull-request, CI, and remote-merge evidence remain authoritative for subsequent publication status. This update does not revise the report's original evidence moment or grant deployment, production/pilot, shared-database, activation, lifecycle/role, external-service, credential, destructive-operation, or Phase 1F implementation authority.

## 2026-07-20 post-merge note

PR #4 passed API and web CI and merged the combined accepted source to `main` at `2239441505cc47235ad387070bcfd7a9e2a2f4c6`. This post-merge note records only the later publication outcome; it does not revise the report's original evidence moment or expand any deployment, production/pilot, shared-database, activation, lifecycle/role, external-service, credential, destructive-operation, or Phase 1F authority.

## Scope

This branch implements the owner-approved Phase 1 administrator/operator workflow refinement:

- exact-application onboarding assignment through readable controls;
- editable unused onboarding plans with ordered task authoring;
- immediate plan content and availability lock after the first assignment reference;
- assignment-bound manual evidence, policy acknowledgements, and e-sign envelope history;
- exactly three manual gates and two derived-only gates;
- provider-authoritative Documenso v2 status refresh and rejected-envelope replacement history;
- server-projected eligible-agent selection, slug availability checks, explicit publication, and permanent first-publication slug reservation;
- removal of the obsolete `/admin/content` placeholder.

The branch does not add final activation, an agent-role grant, a candidate-to-agent transition, Documenso deployment, webhook processing, a CMS, borrower workflows, or production/pilot authority.

## Confirmed implementation boundaries

### Onboarding plans and assignment provenance

- Authorized administrators can create plans and edit names, descriptions, and ordered task definitions while no assignment references the plan.
- Assignment acquisition locks the exact application, candidate, and plan in that order. This serializes same-candidate assignment attempts across different applications and plans while preserving the application-first lock order used by review mutations. A real PostgreSQL race test confirms simultaneous attempts leave exactly one active assignment. The first assignment reference blocks later plan content and availability changes with conflict responses.
- Assignment creation retains the exact candidate, candidate application, plan, and generation provenance. The ordinary operator UI uses readable candidate/application and plan controls rather than raw UUID entry.
- No plan clone, version, or supersession lifecycle was introduced.

### Gates, acknowledgements, and evidence

- Manual administration is limited to `background_check`, `fsra_authorization`, and `system_provisioning`.
- `policy_acknowledgement` and `executed_agreements` are derived-only and reject manual satisfaction or reopening.
- Manual evidence is assignment-bound and records concise source/reference data, verifier, and verification time. Reopening requires a correction reason and appends evidence/audit history.
- Active-assignment and gate rows are locked and refreshed before gate transitions. Real PostgreSQL concurrency evidence confirms that two simultaneous manual satisfaction attempts commit one state transition and one evidence event.
- Policy acknowledgements must reference the exact active assignment and required document version.
- `activation_ready` is calculated for the exact assignment being projected. Superseded assignment history is read-only and cannot inherit readiness from a newer active assignment. There is no activation endpoint or role transition.

### Documenso reconciliation

- Documenso is configured through one exact HTTPS `/api/v2` origin and a separate approved public HTTPS origin.
- The status client URL-quotes the exact envelope identifier, refuses non-HTTPS requests, refuses redirects, bounds response size, allow-lists provider statuses, and returns user-safe failures without token or response-body leakage.
- The current Documenso v2 documentation confirms `GET /api/v2/envelope/{envelopeId}` and statuses `DRAFT`, `PENDING`, `COMPLETED`, and `REJECTED`.
- Only provider-confirmed `COMPLETED` satisfies `executed_agreements`. Rejected predecessors remain historical and non-satisfying when replaced.
- Provider/network failure or an unrepresentable `DRAFT` response reopens the derived gate and records safe audit metadata while preserving the last known envelope status. This prevents prior completion from remaining activation-ready when current verification fails.
- Assignment and envelope rows are locked and refreshed after the network call. Real PostgreSQL concurrency evidence confirms that a delayed completed refresh cannot mutate or satisfy a predecessor that was replaced while the provider call was in flight.
- Exact webhook names, signatures, and deployed-version behavior are not implemented or claimed.

### Agent profiles and content boundary

- Profile creation selects only server-projected eligible active agent relationships.
- Slug syntax and availability are checked server-side.
- First publication permanently records the slug lock. Unpublishing does not release the slug, and later slug mutation is rejected server-side and disabled in the UI.
- Publication remains explicit and eligibility remains server-enforced.
- `/admin/content` and its navigation/route inventory entry are removed. Public content remains repository-controlled.

## Migration and contract evidence

Migration `20260719_0008_admin_operator_workflows.py` advances only from issued revision `20260718_0007`. It adds assignment provenance, gate-evidence history, envelope replacement/current-row controls, and permanent slug-lock data without rewriting issued migration history.

The populated-data migration boundary is explicit and fail-closed:

- upgrade stops before DDL if legacy non-null provider envelope IDs are duplicated because no authoritative row can be selected or rewritten automatically;
- historical first-publication slug locks are recovered from profile state, publication timestamps, or authoritative `agent_profile.published` audit events;
- downgrade stops before DDL if `rejected` envelope rows exist because revision `0007` cannot represent that status without falsifying evidence.

The isolated PostgreSQL verifier completed:

1. blank-database upgrade through `20260719_0008`;
2. current-head assertion;
3. `alembic check` with `No new upgrade operations detected.`;
4. downgrade to `20260718_0007`;
5. re-upgrade to `20260719_0008`;
6. populated upgrade with audit-derived historical slug locking;
7. explicit pre-DDL rejection of duplicate legacy provider envelope IDs;
8. explicit pre-DDL rejection of an unrepresentable rejected-envelope downgrade;
9. real PostgreSQL assignment, refresh/replacement, and gate-transition concurrency races;
10. final head assertion and isolated-database cleanup.

OpenAPI export and `npm run contracts:generate` completed after route/schema stabilization. `packages/contracts/openapi.json` and `packages/contracts/src/generated.ts` are aligned with the candidate API.

## Verification evidence

All commands ran in `/home/john/dev/keeper-financial-admin-ux` unless noted.

| Check                     | Command                                                                                                                                                                                                                                                                         | Result                                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| API lint                  | `.venv/bin/ruff check apps/api/src apps/api/tests apps/api/alembic` using the repository venv                                                                                                                                                                                   | Passed: `All checks passed!`                                                                                      |
| API types                 | `PYTHONPATH=apps/api/src .venv/bin/mypy apps/api/src` using the repository venv                                                                                                                                                                                                 | Passed: `Success: no issues found in 56 source files`                                                             |
| API tests                 | `PYTHONPATH=apps/api/src .venv/bin/pytest apps/api/tests -q` using the repository venv                                                                                                                                                                                          | Exit 0 across the complete API test directory; environment-dependent tests remained skipped                       |
| Web lint                  | `npm run lint`                                                                                                                                                                                                                                                                  | Passed for `@keeper/web` and `@keeper/ui` with zero warnings                                                      |
| Web types                 | `npm run typecheck --workspace @keeper/web`                                                                                                                                                                                                                                     | Passed                                                                                                            |
| Web tests                 | `npm run test --workspace @keeper/web -- --run`                                                                                                                                                                                                                                 | Passed: 28 files passed, 1 file skipped; 142 tests passed, 3 skipped                                              |
| Production build          | `npm run build`                                                                                                                                                                                                                                                                 | Passed; Next.js compiled, typed, generated 35 static pages, and omitted `/admin/content` from the route inventory |
| Formatting                | `npm run format`                                                                                                                                                                                                                                                                | Passed; changed worktree web files were formatted                                                                 |
| Contracts                 | OpenAPI export, `npm run contracts:generate`, contracts formatting                                                                                                                                                                                                              | Passed                                                                                                            |
| Migration and concurrency | `KEEPER_RUN_SCHEMA_MIGRATION_E2E=1 PYTHONPATH=apps/api/src .venv/bin/pytest -o addopts='' apps/api/tests/test_phase1f_schema_drift_migration.py apps/api/tests/test_admin_operator_migration.py apps/api/tests/test_admin_operator_concurrency.py -q` using the repository venv | Passed: 10 isolated PostgreSQL tests, including populated boundaries and real row-lock races                      |
| Diff integrity            | `git diff --check`                                                                                                                                                                                                                                                              | Passed                                                                                                            |

Focused regression evidence includes:

- unused-plan editing and rejection of both content and availability changes after first assignment;
- assignment isolation across multiple applications for one candidate;
- assignment-bound manual evidence and correction history;
- derived-only policy and executed-agreement gates;
- exact-assignment readiness and read-only superseded-assignment history;
- provider-authoritative refresh, fail-closed provider/DRAFT handling, and rejected-envelope replacement history;
- real PostgreSQL serialization of concurrent assignment, manual-gate, and refresh/replacement transitions;
- strict HTTPS/no-redirect Documenso client behavior;
- eligible-agent projection, slug availability, explicit publication, and permanent first-publication locking;
- administrator task authoring/reordering, inactive-plan recovery, historical assignment labeling, and locked-plan UI behavior.

## Browser evidence and limits

A temporary Vite harness imported the actual worktree `OnboardingAdmin` component and supplied deterministic mocked API responses. Profile-local Chrome `151.0.7922.34` rendered the component and verified:

- the unused plan exposed View, Edit, and Deactivate controls;
- the assigned plan exposed View only and displayed `Locked after first assignment.`;
- edit mode populated the plan and ordered task;
- browser typing changed the plan and task titles;
- save returned the editor to create mode and rendered the revised values;
- the browser console remained empty with zero JavaScript errors.

The managed `browser_click` ref dispatcher reported success but did not dispatch React click handlers in the temporary harness. Native DOM `.click()` in the same Chromium session did dispatch them; managed `browser_type` worked. This is recorded as a harness/tool limitation, not hidden as full browser end-to-end evidence.

This browser check does **not** prove the live Supabase login/MFA, PostgreSQL API, Documenso instance, network, email, or production layout integration. The services already running on ports 3000/8000 belonged to the dirty primary checkout and were deliberately rejected as branch evidence. This worktree also lacks the untracked local Supabase signing-key file. Genuine authenticated stack/browser evidence remains an operational prerequisite before pilot acceptance.

## Security review notes

- No final activation operation, candidate-to-agent transition, or new agent-role grant was introduced.
- The only role-grant search result is the pre-existing posting-bound candidate provisioning path.
- A pre-acceptance scan found that the initial Documenso client/configuration accepted HTTP. A red test proved it would attempt network I/O. The branch was repaired to require HTTPS in both settings validation and the client guard; focused and full API verification passed afterward.
- Synthetic credentials remain synthetic test strings. No repository secret, environment credential, or token value is recorded here.

## Documentation synchronization

The branch updates the current source of truth, architecture, security/privacy baseline, domain/lifecycle model, delivery plan, acceptance tests, decisions/open questions, API/data inventory, test strategy, and known limitations. Dated historical reports were preserved as evidence of their original checkpoints.

## Residual risks and stop conditions

- Independent reviews began before the final remediation pass and reported candidate-lock, downgrade, historical-readiness, superseded-replacement, and provider-authority defects. Current code and documents disposition those findings through candidate/assignment/envelope row locks, pre-DDL downgrade refusal, exact-assignment readiness, active-assignment replacement validation, and provider-authoritative decisions. Full deterministic re-verification passed and the owner accepted the Phase 1 source implementation; commit or merge remains separately unauthorized.
- Migration `0008` deliberately refuses ambiguous duplicate legacy provider envelope IDs on upgrade and rejected-envelope evidence on downgrade. Operators must reconcile or export such evidence under an approved procedure before retrying; the migration does not silently deduplicate or relabel it.
- Genuine authenticated stack/browser validation remains outstanding for exact-application assignment, gate correction, provider refresh/replacement, and profile publication.
- The self-hosted Documenso version, credentials, HTTPS routing, deployed endpoint behavior, webhook names/signatures, replacement/void semantics, monitoring, and operator runbook require Phase 1F or conditional-deployment confirmation.
- Production/pilot readiness, legal/privacy/regulatory/claims/accessibility review, backups/restores, incident response, monitoring, email/auth configuration, secrets/access review, and deployment guardrails remain Phase 1F work.
- Passing tests is not pilot or production acceptance.

## Git restrictions

No commit, push, pull request, merge, deployment, shared database mutation, credential rotation, or destructive Git operation was performed. The primary checkout's pre-existing `apps/web/next-env.d.ts` modification was not touched or attributed to this branch.
