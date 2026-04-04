# AGENTS.md

This document provides guidance for agentic coding agents working in this repository.

## Project Overview

This is a pnpm + Turborepo monorepo called "jobs" — a job tracking application with:

- **apps/web** — Next.js 16 (App Router) frontend with React 19, Tailwind CSS 4, shadcn/ui
- **apps/api** — Python FastAPI backend (Python 3.12+, managed by uv), deployed as Vercel Function
- **packages/database** — Prisma ORM package with PostgreSQL
- **packages/ui** — Shared shadcn/ui component library (base-ui/react + CVA)
- **packages/eslint-config** — Shared ESLint flat configs (base, next, react-internal, node)
- **packages/prettier-config** — Shared Prettier config
- **packages/typescript-config** — Shared TypeScript configs

## Build & Run Commands

### Install dependencies

```bash
pnpm install
```

### Root-level (runs across all workspaces via Turborepo)

```bash
pnpm build          # Build all packages/apps
pnpm dev            # Start all dev servers
pnpm lint           # Lint all workspaces
pnpm lint:fix       # Auto-fix lint issues across all workspaces
pnpm format         # Format all files with Prettier
pnpm format:check   # Check formatting without writing
pnpm typecheck      # Type-check all TypeScript workspaces
```

### apps/web (Next.js frontend)

```bash
pnpm --filter web dev          # Start dev server (Turbopack)
pnpm --filter web build        # Production build
pnpm --filter web lint         # ESLint check
pnpm --filter web lint:fix     # ESLint auto-fix
pnpm --filter web typecheck    # TypeScript check (tsc --noEmit)
```

### apps/api (Python FastAPI backend)

```bash
cd apps/api
uv run fastapi dev main.py --host 0.0.0.0 --port 8000   # Dev server
uv run ruff check                                           # Lint
uv run ruff check --fix                                     # Lint auto-fix
uv run ruff format --check                                  # Check formatting
uv run ruff format                                          # Format
uv run pytest tests/ -v                                     # Run all tests
uv run pytest tests/test_foo.py::test_name -v              # Run single test
```

### packages/database (Prisma)

```bash
pnpm --filter @workspace/database db:generate    # Generate Prisma client
pnpm --filter @workspace/database db:push        # Push schema to DB
pnpm --filter @workspace/database db:migrate     # Run migrations
pnpm --filter @workspace/database db:studio      # Open Prisma Studio
pnpm --filter @workspace/database lint           # ESLint check
pnpm --filter @workspace/database typecheck      # TypeScript check
```

### packages/ui (Shared components)

```bash
pnpm --filter @workspace/ui lint         # ESLint check
pnpm --filter @workspace/ui typecheck    # TypeScript check
```

### Adding shadcn/ui components

```bash
pnpm dlx shadcn@latest add <component> -c apps/web
```

Components are placed in `packages/ui/src/components/`.

## Code Style Guidelines

### TypeScript / React

**Formatting (enforced by Prettier):**

- No semicolons
- Double quotes for strings
- 2-space indentation
- 80 character line width
- Trailing commas (ES5: last element in multi-line arrays/objects gets a comma)
- Arrow function parens always: `(x) => x` not `x => x`
- LF line endings

**Imports:**

- Use workspace package imports: `import { Button } from "@workspace/ui/components/button"`
- Use `@/` path alias for web app local imports: `import { ThemeProvider } from "@/components/theme-provider"`
- Relative imports in packages use `.js` extension (NodeNext module resolution): `import { env } from "./env.js"`
- Import React as a namespace: `import * as React from "react"` (not destructured)
- Order: external packages → workspace packages → local/relative imports

**Exports:**

- Prefer named exports over default exports for utilities and components
- Default exports are acceptable for Next.js page/layout components
- Export types alongside values from barrel files

**Components:**

- `"use client"` directive must be the very first line of client components
- Use function declarations for components: `function Button({ ... }) { ... }`
- Use PascalCase for component files: `button.tsx`, `theme-provider.tsx`
- Use kebab-case for non-component files: `utils.ts`, `env.ts`
- Use `cn()` (from `@workspace/ui/lib/utils`) to merge Tailwind classes
- Use CVA (`class-variance-authority`) for component variants

**Types:**

- TypeScript strict mode is enabled everywhere
- `noUncheckedIndexedAccess` is enabled — always handle `undefined` from array/object indexing
- Use `Readonly<{...}>` for component props with `children`
- Use Zod schemas for runtime validation (available in workspace)
- Prefer `interface` for object shapes, `type` for unions/intersections

**Error handling:**

- Use `@t3-oss/env-core` + Zod for environment variable validation (see `packages/database/src/env.ts`)
- Prisma errors should be caught and handled appropriately
- Never expose raw errors to the client

**ESLint:**

- All ESLint rules are set to "warn" only (via `eslint-plugin-only-warn`)
- TypeScript ESLint recommended rules enforced
- React hooks rules enforced
- Next.js core web vitals rules for web app
- `eqeqeq: always` enforced in Node.js contexts
- No `console` restriction in Node.js contexts

### Python (apps/api)

- **Formatter/Linter:** Ruff
- **Python version:** 3.12+
- **Line length:** 88 characters
- **Indent:** 4 spaces
- **Quotes:** Double quotes
- **Lint rules:** E, F, UP, B, SIM, I (some suppressed — see ruff.toml for full list)
- **Testing:** pytest
- **Framework:** FastAPI with Pydantic v2 + Pydantic Settings
- Use snake_case for functions and variables, PascalCase for classes
- Use type hints on all function signatures

### Prisma (packages/database)

- Schema file: `packages/database/prisma/schema.prisma`
- PostgreSQL provider
- Models use PascalCase names, fields use camelCase
- Use `@@map("table_name")` to map models to snake_case table names
- Use `@default(cuid())` for IDs
- Use `@updatedAt` for updated-at timestamps
- Client is singleton-patterned with global cache in dev (see `src/client.ts`)
- Prisma client uses the `@prisma/adapter-pg` adapter

## Key Conventions

1. **Monorepo package naming:** `@workspace/<name>` for all internal packages
2. **Package manager:** pnpm (v9.x) — always use pnpm, never npm or yarn
3. **Node version:** >= 20
4. **Module type:** `"type": "module"` (ESM throughout)
5. **Test single file (Python):** `uv run pytest tests/test_file.py -v`
6. **Test single test case (Python):** `uv run pytest tests/test_file.py::test_name -v`
7. **Do not commit** `.env` files or secrets
8. **Do not add comments** unless explicitly requested or the code is genuinely non-obvious
9. After making changes, always run `pnpm lint`, `pnpm typecheck`, and `pnpm format:check` before considering work done
10. When adding new dependencies, use `pnpm add <pkg> --filter <workspace>` for the correct workspace
