# MortgageApp Porting Manifest

- **Reviewed repository:** `https://github.com/jbelanic/MortgageApp.git`
- **Reviewed branch:** `main`
- **Reviewed commit:** `251077177315ade4a94d12eb62df750684ed2bb7`
- **Review date:** 2026-07-24
- **Target repository:** Keeper Financial at Phase A baseline `5f8a41f34bb3586c59d613848fafc9435a86b50d`
- **Purpose:** provenance and explicit port/reject decisions; no code or data import occurs in Phase A

The legacy repository is a reference, not an implementation dependency. Keeper will reimplement approved concepts in its existing Next.js/FastAPI modular monolith. This document records why no submodule, subtree, Kotlin service, history merge, or live legacy deployment is approved.

## Reviewed architecture

- React/Vite/TypeScript browser application.
- Kotlin/Ktor backend.
- PostgreSQL persistence of a serialized application payload.
- public unauthenticated submission endpoint.
- Turnstile verification attempt.
- Discord webhook notification/delivery path.
- browser local-storage draft persistence.
- no document-upload/MinIO/ClamAV implementation.
- no material automated test suite found at the reviewed revision.

## Port, redesign, or reject

| Legacy concept                                                      | Decision                                           | Keeper target                                                                          |
| ------------------------------------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Step-based mortgage workflow                                        | Port concept and redesign                          | Accessible Next.js flow in Keeper design system                                        |
| Mortgage details and down-payment sources                           | Port typed fields                                  | Versioned borrower schema                                                              |
| Primary/co-applicant collection                                     | Port with an exact maximum of one co-borrower      | Typed encrypted application payload                                                    |
| Applicant contact, date of birth, address, marital/dependant fields | Port after data minimization and validation review | Typed encrypted payload                                                                |
| SIN field                                                           | Port with heightened controls                      | Encrypted, never browser-persisted or logged, masked/AAL2 reveal                       |
| Employment/income entries                                           | Port and normalize validation                      | Typed bounded repeat group                                                             |
| Subject and other-property fields                                   | Port conditionally                                 | Purpose-aware typed groups                                                             |
| Asset/liability entries                                             | Port                                               | Typed bounded repeat groups                                                            |
| Additional notes                                                    | Port with warning and length bound                 | Encrypted sensitive field                                                              |
| Review-before-submit                                                | Port                                               | Server-authoritative revision review                                                   |
| Turnstile/bot mitigation intent                                     | Redesign                                           | Provider result must be validated fail-closed; exact provider is a deployment decision |
| Kotlin/Ktor backend                                                 | Reject                                             | Existing FastAPI modular monolith                                                      |
| Separate Vite deployment                                            | Reject                                             | Existing Next.js application and release process                                       |
| Browser `localStorage` application persistence                      | Reject                                             | Server draft plus secure capability cookie; no sensitive browser storage               |
| Discord webhook with application payload                            | Reject                                             | No payload notification; safe aggregate operational events only                        |
| Success before asynchronous storage finishes                        | Reject                                             | Atomic/idempotent durable submission                                                   |
| Unauthenticated application lookup                                  | Reject                                             | High-entropy capability plus exact draft binding, origin, CSRF, expiry                 |
| Permissive CORS                                                     | Reject                                             | Exact approved origins only                                                            |
| Weak/provider-incomplete Turnstile check                            | Reject                                             | Validate transport and provider-level success/action/host policy                       |
| Logging tokens, validation values, or application data              | Reject                                             | Minimized structured logs and safe audits                                              |
| Unversioned serialized JSON as the lifecycle model                  | Reject                                             | Versioned typed schema, lifecycle metadata, immutable submission snapshot              |
| Typed-name/e-signature control                                      | Reject                                             | Versioned privacy/credit consent only; signatures remain outside Keeper                |
| Hard-coded or conflicting API destinations                          | Reject                                             | One Keeper-owned configuration/routing boundary                                        |
| Secret-shaped/sample credentials in tracked configuration           | Reject                                             | External secret custody; never copy values                                             |
| Unpinned `latest` containers                                        | Reject                                             | Reviewed/pinned deployment versions and digest evidence                                |
| Direct code-history import, submodule, or subtree                   | Reject                                             | Preserve provenance through this manifest and normal Keeper commits                    |

## Security findings that must not cross into Keeper

1. Full application state, including potentially SIN, is stored in browser local storage.
2. Full application data is sent to a Discord webhook.
3. Public submission lacks a safe application ownership/capability model.
4. Submission can report success and clear client state before persistence/delivery is confirmed.
5. Provider-level Turnstile success is not correctly enforced, and related values are logged.
6. CORS is permissive.
7. Persistence lacks explicit lifecycle, retention, legal-hold, consent-version, assignment, and audit models.
8. No private-object, malware-scanning, or document authorization path exists.
9. Secret-shaped values and sample credentials were encountered; their values are intentionally omitted as `[REDACTED]` and must never be copied.
10. No passing legacy test suite establishes a safe behavioral baseline.

## Data migration decision

No legacy production data migration is approved or assumed. Before any future import, the owner must identify the source data, lawful authority, record owners, consent provenance, integrity, malware state, duplicates, retention start dates, legal holds, and reconciliation/rollback method. Without that separate approval, only field concepts are ported.

## Legacy build evidence

At the review checkpoint:

- the combined frontend install/lint/build/audit command exited nonzero; a later isolated build wrapper exited successfully, but retained evidence did not establish passing lint or audit;
- direct Gradle wrapper execution failed because the wrapper was not executable;
- Bash-invoked Gradle reached the build but exited nonzero;
- no legacy tests were found.

These results are historical assessment evidence, not a requirement to repair the legacy application. Keeper-native implementation must establish its own test and security evidence.

## Archive gate

Do not archive the legacy repository until all of the following are owner-accepted:

1. Keeper-native implementation and migration chain;
2. synthetic local end-to-end application, document, assignment, and review evidence;
3. retention/legal-hold and isolated restore evidence;
4. self-hosted Linux deployment and cutover;
5. confirmation that no required data or operational dependency remains in the legacy deployment.

Archival must preserve Git history and be reversible through GitHub's repository unarchive operation. Deletion, force-push, history rewrite, or credential recovery from legacy history is not authorized by this manifest.
