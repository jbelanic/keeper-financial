# Agent referral links

Every onboarded agent account owns exactly one opaque referral code. An
application started from an agent's link is attributed to that agent **and
assigned to them at start**, so no administrator action is needed to route it.

## Prerequisites for a working link

A code resolves to an agent only when all three hold:

- the user account is active;
- the account holds the `agent` role (granted by onboarding completion);
- an **active candidate relationship** exists — the `candidates` row created when
  the person went through the candidate application.

A **published agent profile is not required**. Profile publication is an
independent step that controls the public `/agents` listing, not link eligibility.

If any condition fails — revoked code, inactive user, missing role, inactive
relationship — the application still starts, stays unassigned, and lands in the
administrator queue. The response is identical to a request with no code at all,
so a code cannot be probed for validity and an applicant is never blocked.

## Where the agent gets it

`/agent` → **Your application link** card, with a copy button. The first read
mints the code; nothing is emailed and no notification is sent when a code is
created.

Link shape:

```
{BORROWER_APPLICATION_ORIGIN}/mortgage-application?agent=<code>
```

`BORROWER_APPLICATION_ORIGIN` is the browser-facing application host:
`https://apply.keeperfinancial.ca` in production, `http://apply.localhost:3000`
locally. It must **not** be the API origin (`:8000`) — that has no application
page, and any link built from it dead-ends.

## What the applicant sees

- Opening the link starts a normal accountless draft and shows
  "You are applying with <agent name>".
- Opening the wizard without a link shows an optional free-text field,
  "Are you working with an agent?". That text is stored inside the encrypted
  payload and shown to administrators as an **unverified hint**; it is never
  matched to an account automatically.

## What the administrator sees

The submitted-application review queue shows the assigned agent plus the
attribution source (`via agent link: <name>`), backed by these
`borrower_applications` columns:

| Column | Meaning |
| --- | --- |
| `attribution_source` | `agent_link` when a code resolved |
| `attribution_agent_user_id` | resolved agent account |
| `attribution_referral_link_id` | the exact code used, kept as evidence |
| `attribution_agent_slug` | legacy slug path, when one applied |
| `attribution_resolved_at` | resolution timestamp |

Assignment at start appends `borrower_assignment_history` with
`reason_category = attribution`.

## Assigned-agent draft access

The assigned agent can open an in-progress draft of an application attributed to
them, so they can help the applicant finish it. That view is deliberately
bounded:

- contact details, mortgage request summary, and progress only;
- SIN display-masked;
- **no documents**;
- expired or purged drafts return `404`;
- reads never extend `last_activity_at` or draft retention;
- every read appends a `borrower_application_agent_draft_viewed` audit event.

## Rotation and revocation

| Operation | Endpoint |
| --- | --- |
| Agent reads their own link | `GET /api/v1/agent-referral-link` |
| Administrator reads an agent's link | `GET /api/v1/admin/agent-accounts/{user_id}/referral-link` |
| Administrator rotates (AAL2 required) | `POST /api/v1/admin/agent-accounts/{user_id}/referral-link/rotate` |

Rotation replaces the code immediately: previously shared links stop attributing
new applications, silently and without an error to the applicant. Applications
already attributed keep their original attribution and evidence. Codes are 80 bits
of entropy in an opaque string, so they are not guessable or enumerable.

## Verification queries

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  select l.code, u.email, u.is_active,
         exists(select 1 from user_roles ur join roles r on r.id = ur.role_id
                where ur.user_id = u.id and r.code = '"'"'agent'"'"') as has_agent_role,
         (select count(*) from candidates c where c.user_id = u.id and c.status = '"'"'active'"'"') as active_candidates
  from agent_referral_links l join users u on u.id = l.user_id
  order by l.created_at desc;"'
```

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  select lifecycle_status, attribution_source, attributed_at, assigned_at
  from borrower_applications
  where attribution_source is not null
  order by created_at desc limit 10;"'
```

`has_agent_role` must be true and `active_candidates` at least 1 for a link to
attribute anything.

## Boundaries

- The link carries no applicant identity and grants no access by itself; every
  draft stays capability-bound.
- Attribution never overrides assignment authorization — an administrator can
  still reassign, and the history records who did it.
- Draft review by the assigned agent is not a document-access path. Do not add
  document exposure to it without an approved decision.
