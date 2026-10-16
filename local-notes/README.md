# Local operational notes (private — do not commit)

This directory holds **private, machine-specific operational values** that must never
enter Git. Everything here is gitignored **except this README**, so it survives
`git pull`, branch switches, and `git checkout`.

Keep the tracked runbooks' tables blank (placeholders). Write the real values here:

| Runbook field | Keep private here |
| --- | --- |
| `backup-restore-runbook.md` §0 named operators | `operators.md` |
| `backup-restore-runbook.md` §6 drill/incident log | `incident-log.md` |
| `incident-response.md` contacts / escalation | `operators.md` |
| local `.env` values, hostnames, account details | `secrets-notes.md` (or your password manager) |

Suggested files:

- `operators.md` — the named-operators table, filled in with real names and the
  `ALERT_EMAIL` recipient.
- `incident-log.md` — dated post-incident and restore-drill entries.
