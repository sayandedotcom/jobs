# AGENTS.md

## Architecture

pnpm + Turborepo monorepo — a job aggregation platform with automated scanning agents.

- **apps/web** — Next.js 16 (App Router), React 19, Tailwind CSS 4, shadcn/ui, better-auth
  - Route groups: `app/(auth)/` (login), `app/(main)/` (dashboard, jobs, saved, alerts, agents)
  - `app/api/` — Next.js API routes (auth, BFF proxies to Python API)
  - `lib/auth.ts` — server-side better-auth, `lib/auth-client.ts` — client-side
  - `lib/api-client.ts` — typed client calling the Python API
- **apps/api** — Python FastAPI backend (3.12+, managed by uv)
  - `routers/` — REST endpoints mounted at `/api/*` (jobs, saved, searches, agents, scan, cron)
  - `pipeline/` — LangGraph job-scraping pipeline (fetch → filter → extract → dedup → store)
  - `pipeline/sources/` — pluggable sources (Reddit via asyncpraw)
  - `pipeline/agent_graph.py` — per-agent matching pipeline (LLM via LangChain + Gemini)
  - `core/config.py` — Pydantic Settings reads `.env` directly
  - `core/database.py` — asyncpg pool (separate from Prisma)
- **packages/database** — Prisma ORM with PostgreSQL (`@prisma/adapter-pg`)
- **packages/ui** — Shared shadcn/ui components (base-ui/react + CVA)
- **packages/eslint-config** — Shared ESLint flat configs (base, next, react-internal, node)
- **packages/prettier-config** — Shared Prettier config
- **packages/typescript-config** — Shared TypeScript configs

## Commands

### Root (Turborepo, all workspaces)

```bash
pnpm install
pnpm build
pnpm dev              # all dev servers
pnpm lint
pnpm lint:fix
pnpm typecheck
pnpm format
pnpm format:check
```

### apps/web

```bash
pnpm --filter web dev           # Turbopack dev server
pnpm --filter web lint
pnpm --filter web typecheck     # tsc --noEmit
```

### apps/api (all commands via `uv run`)

```bash
cd apps/api
uv run fastapi dev main.py --host 0.0.0.0 --port 8000
uv run ruff check                # lint
uv run ruff check --fix          # lint auto-fix
uv run ruff format --check       # check formatting
uv run ruff format               # format
uv run pytest tests/ -v                        # all tests
uv run pytest tests/test_filter.py -v          # single file
uv run pytest tests/test_filter.py::test_job_keywords_exist -v  # single test
```

Tests use `pytest-asyncio` — async tests need `@pytest.mark.asyncio`.

### packages/database (Prisma)

```bash
pnpm --filter @workspace/database db:generate   # generate client (also runs on postinstall)
pnpm --filter @workspace/database db:push       # push schema to DB
pnpm --filter @workspace/database db:migrate    # run migrations
```

### Adding shadcn/ui components

```bash
pnpm dlx shadcn@latest add <component> -c apps/web
```

Output goes to `packages/ui/src/components/`. Import as `@workspace/ui/components/<name>`.

## After making changes

Run these before considering work done:

```bash
pnpm lint
pnpm typecheck
pnpm format:check
```

For Python changes, also run inside `apps/api`:

```bash
uv run ruff check && uv run ruff format --check && uv run pytest tests/ -v
```

## Code style — things agents get wrong

### TypeScript / React

- **No semicolons**, double quotes, 2-space indent, 80 char width — enforced by Prettier
- **Relative imports in packages need `.js` extension** (NodeNext resolution): `import { env } from "./env.js"`
- Web app uses `@/` path alias: `import { ThemeProvider } from "@/components/theme-provider"`
- Import React as namespace: `import * as React from "react"`
- `"use client"` must be the very first line of client components
- `noUncheckedIndexedAccess` is on — handle `undefined` from array/object indexing
- All ESLint rules are **warn-only** (via `eslint-plugin-only-warn`) — lint won't block builds
- `eqeqeq: always` enforced in Node.js contexts (database package)

### Python (apps/api)

- **Ruff** for lint + format (not Black, not flake8)
- Line length 88, double quotes, 4-space indent
- Lint rules: E, F, UP, B, SIM, I — several suppressed (see `ruff.toml`)
- Framework: FastAPI + Pydantic v2 + Pydantic Settings
- Pipeline state uses `TypedDict`, API schemas use Pydantic `BaseModel`

### Prisma (packages/database)

- Models: PascalCase names, camelCase fields, `@@map("snake_case")` for table names
- IDs: `@id @default(cuid())` (not uuid)
- Prisma client uses `@prisma/adapter-pg` adapter with a `pg` Pool
- **Singleton pattern** with global cache in dev (see `src/client.ts`)
- `src/env.ts` manually reads repo-root `.env` and validates with `@t3-oss/env-core` + Zod

## Key conventions

- Monorepo packages named `@workspace/<name>`; filter with `pnpm --filter <name>` (web uses `"web"`, database uses `"@workspace/database"`)
- pnpm only — never npm or yarn
- ESM throughout (`"type": "module"`)
- Node >= 20, Python >= 3.12
- New dependencies: `pnpm add <pkg> --filter <workspace>`
- **No comments** in code unless explicitly requested
- Do not commit `.env` files or secrets
- API tests run from `apps/api` directory (not from repo root)
