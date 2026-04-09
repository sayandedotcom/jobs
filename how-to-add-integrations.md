# How to Add a New Integration

Step-by-step guide for adding a new job source to the platform. Follow these in order.

---

## 1. Choose a source name

Pick a lowercase, no-spaces identifier. This name is used everywhere — DB, Python pipeline, frontend config.

| Examples    | Name          |
| ----------- | ------------- |
| LinkedIn    | `linkedin`    |
| Indeed      | `indeed`      |
| 4dayweek.io | `fourdayweek` |

This name must be consistent across:

- `get_source_name()` in Python
- `sources` DB table `name` column
- `SOURCE_CONFIGS` dict key
- `config/source.ts` `id` field (or add an alias — see step 9)

---

## 2. Create the Python source adapter

### Simple source (single API, one file)

Create `apps/api/pipeline/sources/<name>.py`. Use an existing ATS source as a template:

```
apps/api/pipeline/sources/greenhouse.py    ← copy this for simple JSON APIs
apps/api/pipeline/sources/remoteok.py      ← copy this for simple board APIs
```

Minimum structure:

```python
from datetime import datetime
import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.sources.utils import html_to_plain
from pipeline.state import RawPostData


@register_source
class MySourceService(BaseSource):

    def get_source_name(self) -> str:
        return "mysource"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                # ... fetch from API, build RawPostData dicts
                pass
        return posts
```

### Complex source (multiple strategies/parsers → use a folder)

If the source has multiple fetch strategies, parsers, or is 200+ lines, create a package:

```
apps/api/pipeline/sources/hackernews/
├── __init__.py       # re-exports the service class
├── source.py         # HackerNewsService class (overrides BaseSource hooks)
├── algolia.py        # "Who is Hiring?" fetch logic
├── firebase.py       # Job stories fetch logic
├── parser.py         # HTML parsing, text normalization
└── constants.py      # API URLs, limits
```

Reference: `apps/api/pipeline/sources/hackernews/` for the full pattern.

---

## 3. Override behavioral hooks (if needed)

`BaseSource` has three hooks with sensible defaults. Override only if your source needs different behavior:

```python
class MySourceService(BaseSource):

    # Skip keyword filter if ALL posts from this source are job-related
    def skip_keyword_filter(self) -> bool:
        return True

    # Skip embedding dedup if posts have unique, stable external IDs
    def use_embedding_dedup(self) -> bool:
        return False

    # Customize how posts map to DB listing rows
    def build_listing_payload(self, post: RawPostData, item: dict) -> dict:
        metadata = dict(post.get("metadata") or {})
        # ... custom title derivation, metadata enrichment
        return {
            "title": ...,
            "company": ...,
            "description": post["raw_content"],
            "location": None,
            "salary": None,
            "url": post.get("permalink"),
            "jobType": None,
            "applyUrl": None,
            "embeddingText": item.get("embedding_text"),
            "metadata": metadata,
        }
```

Do NOT add `if source_name == "..."` checks in pipeline nodes. Use these hooks instead.

---

## 4. Register the source

### Python import registration

Add to `apps/api/pipeline/sources/__init__.py`:

```python
import pipeline.sources.mysource  # noqa: F401
```

If using a package folder:

```python
import pipeline.sources.mysource.source  # noqa: F401
```

### Source configs

Add to `apps/api/pipeline/source_configs.py`:

```python
SOURCE_CONFIGS: dict[str, dict] = {
    # ... existing sources
    "mysource": {},  # add if no config needed
    # OR if API keys are needed:
    "mysource": {
        "api_key": settings.MYSOURCE_API_KEY,
    },
}
```

If you added env vars, add them to `apps/api/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings
    MYSOURCE_API_KEY: str = ""
```

---

## 5. Add shared utilities if needed

- **HTML stripping**: `from pipeline.sources.utils import html_to_plain` — do NOT define a local `_html_to_plain`
- **Cosine similarity**: `from pipeline.sources.utils import cosine_similarity` — do NOT define a local one

---

## 6. Seed the database

Add to `packages/database/prisma/seed.ts`:

```typescript
const mySource = await prisma.source.upsert({
  where: { name: "mysource" },
  update: {},
  create: {
    name: "mysource",
    type: "mysource",
  },
})

// Add sub-sources (feeds/boards/channels)
await prisma.subSource.upsert({
  where: {
    sourceId_name: {
      sourceId: mySource.id,
      name: "default",
    },
  },
  update: {},
  create: {
    sourceId: mySource.id,
    name: "default",
    // type: "board",  // optional, defaults to "subreddit" in schema
  },
})
```

Then run:

```bash
pnpm --filter @workspace/database db:seed
```

---

## 7. Add frontend source config

Add to `apps/web/config/source.ts`:

```typescript
export const source: Source[] = [
  // ... existing sources
  {
    index: 29, // next available number
    id: "mysource",
    name: "My Source",
    src: "https://cdn.brandfetch.io/.../icon.png",
    active: true, // set to true to enable
    url: "https://mysource.com",
  },
]
```

### If the frontend `id` differs from the DB `sourceName`

Only do this if there's a naming conflict. Add an alias in `apps/web/lib/source-mapping.ts`:

```typescript
export const SOURCE_ID_ALIASES: Record<string, string> = {
  hackernews: "ycombinator",
  mysource: "mysource_frontend_id", // DB name → frontend config id
}
```

Prefer making them match instead of adding aliases.

---

## 8. Add a card component (if needed)

### Default: GenericCard handles it

If your source doesn't need custom rendering, it automatically falls through to `GenericCard`. No code needed.

### Custom card

Create `apps/web/components/cards/<name>-card.tsx`:

```tsx
"use client"

import * as React from "react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@workspace/ui/components/card"
import { type Listing } from "@/lib/api-client"
import { useSaveJob } from "@/components/cards/use-save-job"
import { ShowMoreText } from "@/components/cards/show-more-text"
import { SourceBar } from "@/components/cards/source-bar"
import { CardDateFooter } from "@/components/cards/card-date-footer"

interface MySourceMetadata {
  department?: string | null
  tags?: string[] | null
}

export function MySourceCard({ job }: { job: Listing }) {
  const { saved, handleSave } = useSaveJob(job)
  const meta = (job.metadata as MySourceMetadata | null) ?? {}

  return (
    <Card className="hover:bg-accent/50 transition-colors">
      <SourceBar
        sourceName={job.sourceName}
        saved={saved}
        onSave={handleSave}
      />
      <a
        href={job.url || `/jobs/${job.id}`}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <CardHeader>
          <CardTitle className="leading-tight">{job.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <ShowMoreText text={job.description} />
        </CardContent>
      </a>
      <CardDateFooter date={job.postedAt} />
    </Card>
  )
}
```

### Register the card

Add to `apps/web/components/cards/index.tsx`:

```typescript
import { MySourceCard } from "@/components/cards/mysource-card"

const CARD_REGISTRY: Record<string, React.ComponentType<{ job: Listing }>> = {
  reddit: RedditCard,
  hackernews: HackerNewsCard,
  mysource: MySourceCard, // key must match get_source_name()
}
```

---

## 9. Add a source label suffix (optional)

If the source needs a descriptive badge suffix (like "Who is hiring?" for HN), add to `apps/web/components/cards/source-bar.tsx`:

```typescript
const SOURCE_LABEL_SUFFIX: Record<string, string> = {
  hackernews: "Who is hiring?",
  // mysource: "Board Label",
}
```

---

## 10. Write tests

Create `apps/api/tests/test_mysource_source.py`:

```python
from pipeline.sources.mysource import MySourceService


def test_source_name():
    service = MySourceService()
    assert service.get_source_name() == "mysource"


def test_skip_keyword_filter_default():
    service = MySourceService()
    assert service.skip_keyword_filter() is False
```

Run:

```bash
cd apps/api && uv run pytest tests/test_mysource_source.py -v
```

---

## 11. Verify end-to-end

```bash
# Python lint + format
cd apps/api && uv run ruff check && uv run ruff format --check

# Python tests
cd apps/api && uv run pytest tests/ -v

# TypeScript typecheck
pnpm --filter web typecheck

# Full monorepo lint
pnpm lint
```

Then trigger a scan from the admin page (`/admin`) or via curl:

```bash
# The source param must match the DB sourceName (not the frontend config id)
curl -X POST http://localhost:8000/api/scan/trigger?source=mysource
```

---

## 12. Admin page — scan triggers

The admin page at `/admin` shows all sources from `config/source.ts` and lets you trigger scans.

### How it works

```
Admin page (source.id = "ycombinator")
  → POST /api/scan/trigger?source=ycombinator   (BFF in apps/web)
    → sourceIdToSourceName("ycombinator") = "hackernews"
    → POST PYTHON_API_URL/api/scan/trigger?source=hackernews  (Python API)
      → Looks up "hackernews" in sources DB table
      → Creates scan_runs row
      → Runs pipeline: fetch → filter → dedup → store
```

Key files:

- `apps/web/app/(admin)/admin/page.tsx` — UI with per-source scan buttons + "Scan All"
- `apps/web/app/api/scan/trigger/route.ts` — BFF proxy, translates frontend id → DB sourceName
- `apps/api/routers/scan.py` — Python endpoint that runs the pipeline

### "Scan All" behavior

- Only triggers scans for sources with `active: true` in `config/source.ts`
- Runs all scans in parallel via `Promise.allSettled`

### When adding a new source

If you set `active: true` in `config/source.ts`, the source will:

- Appear in the admin page grid
- Be included in "Scan All"
- Show up in the jobs page source filter dropdown

If `active: false`, the source still appears in admin (for manual scanning) but is excluded from "Scan All" and the jobs filter.

### Scan trigger requirements

For a scan to succeed, the source must have:

1. A row in the `sources` DB table (via `seed.ts`)
2. At least one row in `sub_sources` (the feeds/channels to fetch from)
3. The Python source adapter registered and importable

If any of these are missing, the scan will fail with a 404 or return 0 posts.

---

## Checklist

- [ ] Source adapter created in `pipeline/sources/`
- [ ] Registered in `pipeline/sources/__init__.py`
- [ ] Config added to `pipeline/source_configs.py`
- [ ] Env vars added to `core/config.py` (if needed)
- [ ] DB seeded in `packages/database/prisma/seed.ts`
- [ ] Frontend config added to `apps/web/config/source.ts`
- [ ] Alias added to `apps/web/lib/source-mapping.ts` (only if names differ)
- [ ] Custom card created (or GenericCard is sufficient)
- [ ] Card registered in `apps/web/components/cards/index.tsx` (if custom)
- [ ] Label suffix added to `source-bar.tsx` (if needed)
- [ ] Tests written
- [ ] Lint, format, typecheck all pass
- [ ] Source appears on `/admin` page with correct Active/Inactive badge
- [ ] Manual scan from `/admin` succeeds
- [ ] "Scan All" includes the source (if `active: true`)

---

## Architecture reference

```
Python Pipeline (fetch → filter → dedup → store):
  pipeline/sources/<name>.py          Simple source (single file)
  pipeline/sources/<name>/            Complex source (package)
      __init__.py
      source.py                       Service class + BaseSource overrides
      constants.py                    API URLs, pagination limits
      parser.py                       Text extraction, normalization
      <strategy>.py                   Per-strategy fetch logic

  pipeline/sources/base.py            BaseSource (hooks + contract)
  pipeline/sources/utils.py           Shared html_to_plain, cosine_similarity
  pipeline/sources/registry.py        @register_source decorator
  pipeline/source_configs.py          Constructor kwargs per source
  pipeline/nodes/filter.py            Keyword filter (checks skip_keyword_filter)
  pipeline/nodes/dedup.py             Exact + embedding dedup (checks use_embedding_dedup)
  pipeline/nodes/store.py             DB inserts (calls build_listing_payload)

Frontend:
  config/source.ts                    Source metadata (id, name, icon, active)
  lib/source-mapping.ts               Centralized name aliases
  components/cards/index.tsx          CARD_REGISTRY map
  components/cards/<name>-card.tsx    Custom card (or GenericCard fallback)
  components/cards/source-bar.tsx     SOURCE_LABEL_SUFFIX
```

## Rules

1. **No hardcoded source checks in pipeline nodes** — use BaseSource hooks
2. **No local `_html_to_plain`** — import from `pipeline.sources.utils`
3. **No local `_cosine_similarity`** — import from `pipeline.sources.utils`
4. **No alias duplication** — all aliases go in `lib/source-mapping.ts` only
5. **Source-specific data in `metadata` JSON** — no new DB columns per source
6. **No LLM in default ingestion** — deterministic parsing only
7. **All SQL column names are camelCase** — `"sourceId"`, `"createdAt"`, etc.
8. **All INSERTs need explicit `id` via `cuid()`** — Prisma's `@default` only works through Prisma client
9. **All datetimes must have `tzinfo=None`** before passing to asyncpg — Neon uses `timestamp without time zone`
