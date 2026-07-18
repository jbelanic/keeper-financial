# Phase 1F Step 9 Schema-Drift Report

**Date:** 2026-07-18  
**Branch:** `fix/phase-1d-schema-model-drift`  
**Starting HEAD:** `dddf34758fa48becd8b292eb86b0cf439f9b968c`  
**Starting database head:** `20260717_0006`  
**New revision:** `20260718_0007`  
**Status:** uncommitted owner-review worktree; validation evidence recorded
below does not grant launch approval.

## Scope and authority reconciliation

This Step 9 change resolves only the known Phase 1D SQLAlchemy/Alembic index
and foreign-key delete-action drift. It does not alter candidate
authentication, MFA, application lifecycle behavior, MinIO, ClamAV, API
contracts, document scanning, e-signature behavior, activation readiness, or
final activation.

The current source of truth requires immutable issued migrations,
application-specific and assignment-generation history, exact-version policy
acknowledgements, append-oriented audit evidence, and application-controlled
user/lifecycle deactivation. Those requirements govern this disposition.

The candidate-completion implementation is committed and pushed at
`dddf347`, as confirmed by Git and the owner-provided baseline. Historical
report text that still calls that prior worktree uncommitted is stale evidence;
it was not edited in this bounded schema task.

## Pre-edit baseline

- Branch and upstream were both
  `fix/phase-1d-schema-model-drift`; ahead/behind was `0/0`; the worktree was
  clean.
- `docker compose run --rm api alembic current --check-heads` passed and
  reported `20260717_0006 (head)`.
- `make migrate-check` reproduced all and only the seven known drift groups:
  two proposed simple indexes, removal of the assignment composite index,
  three FK delete-action replacements, and the programmatic-gate composite to
  simple-index replacement.
- PostgreSQL catalog inspection confirmed all affected indexes, stable FK
  names, `NO ACTION` on the three drifted FKs, reviewer nullability, and zero
  orphan rows.
- The local affected tables contained five information-request rows and no
  rows in the other affected tables. No row contents or production data were
  used.

## Authoritative disposition

| Object                                                          | Database before Step 9                                                                                                                        | SQLAlchemy before Step 9                                                                                   | Origin                                | Query/use pattern                                                                                                                                          | Lifecycle, retention, and performance analysis                                                                                                                                                    | Authoritative definition                                                                                                 | Model change                                               | Forward migration                                              | Downgrade                                             | Data-safety risk                                                                                  |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Candidate e-sign envelope candidate index                       | `ix_candidate_esign_envelopes_candidate(candidate_id, created_at, id)`                                                                        | Same composite plus `candidate_id index=True`, which proposed `ix_candidate_esign_envelopes_candidate_id`  | `0004`                                | Filter by candidate and order by `created_at DESC, id DESC`                                                                                                | The composite directly supplies filtering and ordering; a candidate-only btree duplicates its left prefix                                                                                         | Preserve only `ix_candidate_esign_envelopes_candidate(candidate_id, created_at, id)`                                     | Remove `index=True`; retain named composite metadata       | None; schema was already authoritative                         | None                                                  | None                                                                                              |
| Candidate information-request candidate index                   | `ix_candidate_information_requests_candidate_open(candidate_id, created_at, id)` plus the `0006` application index                            | Same composite plus `candidate_id index=True`, which proposed a simple index                               | `0004`; application index from `0006` | Candidate-visible open requests filter by application/status/order; candidate-wide administrative history is candidate/time/id                             | Application queries retain their application index. Candidate-wide history is covered by the composite left prefix and ordering; the simple index is redundant                                    | Preserve the candidate/time/id composite and application index; reject the candidate-only index                          | Remove candidate `index=True`                              | None                                                           | None                                                  | None                                                                                              |
| Candidate onboarding assignment candidate/plan/generation index | Non-unique `ix_candidate_onboarding_assignments_candidate_plan` and an automatically backed unique constraint on the exact same three columns | Unique constraint only                                                                                     | `0004`                                | Candidate/current lookups and `max(generation)` for one candidate/plan; duplicate prevention                                                               | The unique-constraint btree has identical keys/order and provides lookup, generation ordering, and uniqueness. Keeping both doubles write/storage maintenance without a distinct query capability | Keep `UNIQUE(candidate_id, onboarding_plan_id, generation)` and its backing btree; remove the duplicate non-unique index | No additional index metadata; retain the unique constraint | Drop only `ix_candidate_onboarding_assignments_candidate_plan` | Recreate that exact non-unique index                  | Brief index-drop lock; no rows or uniqueness removed                                              |
| Candidate task → onboarding task template FK                    | Named FK `candidate_onboarding_tasks_onboarding_task_id_fkey`, default `NO ACTION`                                                            | Proposed `ON DELETE CASCADE`                                                                               | `0001`                                | Assigned task instances join the exact reusable task definition; activation readiness checks required-template status                                      | There is no template-delete API. Plans/templates are lifecycle-controlled. Cascade could erase completed, submitted, or reviewed candidate evidence                                               | Same stable name with explicit `ON DELETE RESTRICT`                                                                      | Add stable name and replace cascade with restrict          | Drop/recreate named FK as `RESTRICT`                           | Restore same name without delete clause (`NO ACTION`) | Existing FK and explicit orphan check prove valid rows; brief FK-validation/table-lock cost       |
| Candidate task → reviewer user FK                               | Named FK `candidate_onboarding_tasks_reviewed_by_user_id_fkey`, default `NO ACTION`; column nullable                                          | Proposed `ON DELETE SET NULL`                                                                              | `0001`                                | Reviewer is written on administrative task review and displayed as retained task evidence                                                                  | Users have `is_active`; no hard-delete/offboarding API exists. `SET NULL` would discard reviewer attribution, and audit actor links may also null. Null remains necessary before review           | Same stable name with `ON DELETE RESTRICT`; nullable column retained                                                     | Add stable name and use restrict                           | Drop/recreate named FK as `RESTRICT`                           | Restore same name and `NO ACTION`                     | Existing reviewer links remain unchanged; hard deletion is denied, deactivation remains available |
| Policy acknowledgement → document version FK                    | Named FK `policy_acknowledgements_document_version_id_fkey`, default `NO ACTION`                                                              | Proposed `ON DELETE RESTRICT`                                                                              | `0001`                                | Acknowledgement and activation-readiness queries depend on the exact assigned/accepted version                                                             | Issued versions are immutable and acknowledgement evidence must never lose its version. Cascade and nulling are prohibited                                                                        | Same stable name with explicit `ON DELETE RESTRICT`                                                                      | Add stable name; retain restrict                           | Drop/recreate named FK as `RESTRICT`                           | Restore same name and `NO ACTION`                     | Existing FK and orphan check prove valid rows; deletion becomes explicitly denied                 |
| Programmatic-gate candidate index                               | `ix_programmatic_gates_candidate(candidate_id, created_at, id)` plus unique `(candidate_id, code)`                                            | Unique constraint plus candidate `index=True`, proposing removal of composite and addition of simple index | `0004`                                | Current list filters candidate and orders code; gate mutation filters candidate/code; historical/time ordering remains a supported evidence access pattern | Unique `(candidate_id, code)` supplies the current code-ordered path. The historical composite supplies candidate/time/id ordering. A simple candidate index adds no distinct capability          | Preserve the composite and unique constraint; reject the candidate-only index                                            | Add named composite metadata and remove `index=True`       | None; schema was already authoritative                         | None                                                  | None                                                                                              |

## Exact authoritative definitions

Indexes relevant to the original drift:

```text
ix_candidate_esign_envelopes_candidate
  (candidate_id, created_at, id)

ix_candidate_information_requests_candidate_open
  (candidate_id, created_at, id)

UNIQUE candidate_onboarding_assignments
  (candidate_id, onboarding_plan_id, generation)

ix_programmatic_gates_candidate
  (candidate_id, created_at, id)

UNIQUE programmatic_gates
  (candidate_id, code)
```

The following rejected indexes are absent at head:

```text
ix_candidate_esign_envelopes_candidate_id
ix_candidate_information_requests_candidate_id
ix_candidate_onboarding_assignments_candidate_plan
ix_programmatic_gates_candidate_id
```

The assignment name above is absent only for the redundant non-unique index;
the unique-constraint backing index on the same ordered columns remains.

Foreign keys:

```text
candidate_onboarding_tasks_onboarding_task_id_fkey
  onboarding_task_id -> onboarding_tasks.id ON DELETE RESTRICT

candidate_onboarding_tasks_reviewed_by_user_id_fkey
  reviewed_by_user_id -> users.id ON DELETE RESTRICT
  reviewed_by_user_id remains nullable

policy_acknowledgements_document_version_id_fkey
  document_version_id -> document_versions.id ON DELETE RESTRICT
```

## Query-plan review

With sequential scans disabled only to demonstrate index eligibility on the
small local dataset, PostgreSQL selected:

- the e-sign composite for candidate/newest-first retrieval;
- the information-request composite for candidate/time/id history;
- the assignment composite for candidate/plan `max(generation)` before Step 9;
- the programmatic-gate composite for candidate/time/id order; and
- the unique candidate/code index for the current code-ordered gate query.

After the duplicate assignment index is removed, the structurally identical
unique-constraint btree remains eligible for the generation query. These plans
prove key/order compatibility, not production-scale performance; the local
tables are too small for meaningful latency conclusions.

## Migration and downgrade design

`20260718_0007_phase_1f_schema_drift.py` is the only new revision and has
`down_revision = "20260717_0006"`. Upgrade and downgrade use explicit existing
constraint/index names. PostgreSQL executes the DDL transactionally.

Upgrade:

1. Drops the exact duplicate assignment index.
2. Replaces the task-template FK with explicit `RESTRICT`.
3. Replaces the task-reviewer FK with explicit `RESTRICT`.
4. Replaces the acknowledgement-version FK with explicit `RESTRICT`.

Downgrade reverses those operations to the exact `0006` schema: the three
named FKs return to no-clause/default `NO ACTION`, and the redundant named
assignment index is recreated with the original column order.

No column, row, uniqueness rule, migration-version row, or issued migration is
manually rewritten. Existing FKs already guarantee referential integrity; the
pre-edit catalog query independently confirmed zero orphans.

## Tests and validation evidence

`test_phase1f_schema_drift_migration.py` adds:

- immutable SHA-256 assertions for migrations `0001` through `0006`;
- one-head/revision-chain assertions;
- exact SQLAlchemy index/FK metadata assertions;
- isolated PostgreSQL `0006 → 0007 → 0006 → 0007` coverage;
- representative synthetic assignment/task/reviewer/version/
  acknowledgement/information-request/envelope/gate evidence survival;
- PostgreSQL catalog assertions for index names/columns/order, rejected-index
  absence, FK delete action, and reviewer nullability;
- destructive-parent deletion rejection for a referenced task template,
  reviewer, and acknowledged document version;
- clean Alembic autogeneration after re-upgrade; and
- a separate direct fresh-database upgrade to head.

Validation completed during implementation:

| Command/check                                                     | Result                                                                                                                                                                                                                                                        |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Focused metadata/migration tests without opt-in PostgreSQL        | Passed: `2 passed, 2 skipped` before the two existing head assertions were advanced; affected migration tests then passed: `5 passed, 2 skipped`                                                                                                              |
| `KEEPER_RUN_SCHEMA_MIGRATION_E2E=1` focused suite                 | Passed: `4 passed`; includes isolated upgrade/downgrade/re-upgrade, destructive-parent denial, catalog assertions, Alembic check, and direct fresh upgrade                                                                                                    |
| Current local database upgrade                                    | Passed: `0006 → 0007`                                                                                                                                                                                                                                         |
| Current local database downgrade                                  | Passed: `0007 → 0006`; catalog showed the original assignment index restored and all three FKs returned to `confdeltype='a'` / `NO ACTION`                                                                                                                    |
| Current local database re-upgrade                                 | Passed: `0006 → 0007`; final database head is `20260718_0007`                                                                                                                                                                                                 |
| Final current-database catalog/count checks                       | Passed: authoritative indexes/FKs present, rejected indexes absent, the assignment generation plan uses the retained unique btree, all pre-existing affected-table counts unchanged, and all three orphan counts zero                                         |
| `make migrate-check`                                              | Before upgrade, correctly reported `Target database is not up to date` while the database remained at `0006`; after upgrade and again after the downgrade/re-upgrade cycle, passed exactly: `No new upgrade operations detected.`                             |
| `make lint`                                                       | Passed; ESLint and Ruff reported no errors                                                                                                                                                                                                                    |
| `make typecheck`                                                  | Passed; TypeScript and mypy reported no errors in 55 API source files                                                                                                                                                                                         |
| `make test`                                                       | Passed after advancing the two affected old head assertions: web `139 passed, 3 skipped`; API `336 passed, 4 skipped`                                                                                                                                         |
| `make build`                                                      | Passed; Next.js production build completed with 36 static pages generated                                                                                                                                                                                     |
| `make openapi` twice                                              | Passed; both runs reproduced `openapi.json` SHA-256 `d4e114aa98b1faa1fc3fd546a2e94964be042db544f19eb4b68026c9999d6ece` and generated TypeScript SHA-256 `9bd9a3c8f18472131e01781b13721fa61ab0bc7eaa68d6cf1d2f75716aefb17e`; generated contracts are unchanged |
| `docker compose config --quiet` and tracked `.env.example` config | Passed                                                                                                                                                                                                                                                        |
| API/database/MinIO/ClamAV health                                  | Passed: API `status=ok`, database `reachable`, MinIO live probe successful, ClamAV clean sample accepted and standard test marker detected                                                                                                                    |
| Changed-file Ruff format/check and documentation Prettier         | Passed                                                                                                                                                                                                                                                        |
| `git diff --check`                                                | Passed                                                                                                                                                                                                                                                        |
| Issued migration SHA-256 hashes                                   | Unchanged from the pre-edit baseline for `0001` through `0006`                                                                                                                                                                                                |

A whole-tree `ruff format --check apps/api` additionally identified four
pre-existing formatting candidates outside this Step 9 diff:
`main.py`, `sensitive_uploads.py`, `test_phase1e_agents.py`, and
`test_sensitive_upload_middleware.py`. They were deliberately not reformatted
because this task prohibits unrelated changes; all changed Python files pass
Ruff formatting and lint.

## Lock/runtime and residual risk

- Dropping a PostgreSQL index and replacing each FK requires brief table/index
  locks. FK creation validates referencing rows. The current local tables are
  empty except for five information-request rows, and all orphan checks passed;
  nevertheless a future retained database should schedule this migration in a
  controlled maintenance window.
- `RESTRICT` and the prior non-deferrable `NO ACTION` both reject immediate
  referenced-parent deletion in current PostgreSQL use. Step 9 makes the
  retention intent explicit and prevents later metadata drift; it does not add
  a hard-delete workflow.
- Final legal retention periods, legal holds, deletion/de-identification jobs,
  database privilege separation, tamper evidence, backup/restore, operational
  hardening, and owner release approval remain separate Phase 1F gates.
- This uncommitted worktree is not an approved checkpoint until owner review
  and commit. No commit or push was performed by the implementation agent.
