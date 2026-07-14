# Start Here — Windows, WSL, VS Code, and Codex CLI

> Phase 0 has now been scaffolded. For the current runnable setup, use `README.md` and `docs/LOCAL_DEVELOPMENT.md`; the steps below are retained as the original repository-bootstrap record.

## 1. Create the fresh project directory

From the WSL terminal:

```bash
mkdir -p ~/dev/keeper-financial
cd ~/dev/keeper-financial
git init
code .
```

Open VS Code in WSL mode. Confirm the bottom-left remote indicator shows the active WSL distribution.

## 2. Copy this baseline pack into the repository

Copy:

- `README.md`
- `START_HERE_WSL.md`
- `INITIAL_CODEX_PROMPT.md`
- the entire `docs/` directory

into `~/dev/keeper-financial`.

Then run:

```bash
git add README.md START_HERE_WSL.md INITIAL_CODEX_PROMPT.md docs
git commit -m "docs: establish Keeper Financial phase 1 baseline"
```

## 3. Recommended initial repository shape

Codex should create this structure rather than relying on manual scaffolding:

```text
keeper-financial/
├── apps/
│   ├── web/                  # React/TypeScript public site and authenticated portal
│   └── api/                  # FastAPI application
├── packages/
│   ├── ui/                   # shared UI components and design tokens
│   ├── config/               # shared lint/type/config packages where justified
│   └── contracts/            # generated or shared API contracts
├── infrastructure/
│   ├── docker/
│   └── scripts/
├── docs/
├── storage/
│   └── dev_uploads/          # local development only; never nonlocal
├── .env.example
├── compose.yaml
├── Makefile
└── README.md
```

## 4. Recommended frontend decision

Use one React/TypeScript application for Phase 1, with server-rendered or pre-rendered public pages and authenticated portal routes.

Preferred default:

- Next.js with TypeScript for the web application.
- FastAPI for the application API.
- PostgreSQL for application data.
- SQLAlchemy and Alembic.
- Hosted Supabase Auth for nonlocal identity.
- Local Supabase CLI for local identity.
- Private Cloudflare R2 for nonlocal candidate documents.
- Docker Compose for local supporting services.

Reason: the public site, recruiting pages, and agent profile pages need reliable SEO and social previews. A client-only Vite SPA should not be the default public-site architecture. If the final approved UI implementation requires Vite, Codex must document the SEO/pre-rendering strategy before changing this decision.

## 5. Local prerequisites

Recommended:

```bash
git --version
node --version
npm --version
python3 --version
docker --version
docker compose version
supabase --version
codex --version
```

Do not install secrets into the repository. Do not copy production credentials into local `.env` files.

## 6. Initial branch

```bash
git checkout -b phase/01-foundation
```

## 7. Run Codex

From the repository root, start Codex and provide the entire contents of `INITIAL_CODEX_PROMPT.md`.

Codex should stop after the requested foundation phase, summarize the result, list commands run, list tests, identify unresolved decisions, and leave the repository in a reviewable state.

## 8. Review before accepting code

Confirm:

- The source-of-truth documents were not contradicted.
- No mortgage-application or borrower-document storage was created.
- No custom e-signature implementation was created.
- No fake vendor integration was created.
- Authentication and authorization are separate.
- Candidate documents are private.
- Public forms collect only approved minimal data.
- Tests cover authorization boundaries and lifecycle transitions.
- The UI uses the supplied mockup as a visual reference without hard-coding inaccessible or fragile layouts.

## 9. First commit after Codex

Do not blindly commit everything. Review the diff first:

```bash
git status
git diff --stat
git diff
```

Then run the documented validation commands. If acceptable:

```bash
git add .
git commit -m "feat: establish Keeper Financial phase 1 application foundation"
```
