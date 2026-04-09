# Source-Based Job Integration Architecture

## Summary

Design the system as source-first, not canonical-first.

Each integration keeps its own source-shaped payload and card behavior. The backend shares only a very small common base so the app can list jobs, save jobs, sort by recency, and route to details. Do not try to fully
normalize all jobs into one universal schema. Do not add an LLM step to the default ingestion path.

This fits your stated product better:

- source-based cards are the main UI model
- duplicates across sources are allowed as separate cards
- filtering stays basic, not deeply normalized
- onboarding a new source should mostly mean adding one adapter and one card renderer

## Recommended Data Model

Use a shared base table + per-source payload model.

Recommended minimal tables:

- sources
  One row per integration like reddit, remoteok, greenhouse, rss_company_x.
- source_feeds
  One row per feed/channel/query/company board/subreddit/RSS URL.
- jobs
  One row per fetched item shown in the UI.
  This is not a deeply normalized canonical job table. It is a thin shared listing table.
- scan_runs
  One row per scan execution.

Keep jobs minimal. Suggested columns:

- id
- source_id
- source_feed_id
- external_id
- source_name
- card_type
- title
- company
- location_text
- posted_at
- source_url
- apply_url
- summary_text
- raw_payload JSONB
- raw_text
- fetched_at
- last_seen_at
- status

Important rules:

- unique on (source_feed_id, external_id)
- no new column for every new source field
- source-specific data goes into raw_payload
- card_type decides which frontend card component renders the row

This gives you one cheap table for storage while still preserving source-specific UI.

## Ingestion Pipeline

Each source should implement the same pipeline contract, but not the same field shape.

Flow:

1. fetch from source
   Support different adapter families:
   JSON API, RSS, HTML scrape, GitHub content, social API
2. parse raw response
   Convert raw item into a source job object
3. extract only the shared base fields
   Required base extraction:
   external_id, title, company if available, posted_at if available, source_url, apply_url, summary_text, raw_payload, raw_text
4. assign card_type
   Usually same as source_name, unless multiple sources share one card renderer
5. exact dedup within that source/feed
   Use (source_feed_id, external_id)
6. insert or update the jobs row
   Update last_seen_at when the job is seen again
7. render source-specific cards from card_type + raw_payload

Do not run LLM extraction in this default flow.

## Card Architecture

Make the frontend intentionally source-based.

Recommended rendering contract:

- one shared card shell for common chrome
- one card renderer per source or per source family
- card receives:
  title, company, location_text, posted_at, source_url, apply_url, summary_text, raw_payload, source_name, card_type
- source-specific card reads extra fields from raw_payload

Examples:

- Reddit card uses subreddit, score, author, body preview
- RSS card uses feed title, category, author, snippet
- Greenhouse card uses department, team, office, requisition metadata
- Lever card uses commitment, team, workplace type

This means you can keep your existing idea of different integration cards without forcing the database schema to change every time.

## Schema Philosophy

Your original idea of “if a new integration has more fields, create a new row/column” should be adjusted:

Use this rule instead:

- if the field is only useful for that source, keep it in raw_payload
- if the field becomes common across many sources and you want to filter/sort on it, promote it later to a shared column

Promote fields only when all three are true:

1. appears in many sources
2. needed in main UI/search/filter
3. worth indexing/querying

Examples of fields worth eventual promotion:

- company
- location_text
- posted_at
- job_type only if many sources provide it reliably
- salary_min / salary_max only if enough sources support it cleanly

Examples that should usually stay in raw_payload:

- subreddit
- score/upvotes
- department tree
- board-specific tags
- recruiter handles
- feed author details
- custom badges unique to one source

## Dedup Strategy

Because you want separate source-based cards, dedup should stay conservative.

Recommended policy:

- dedup only within the same source feed by exact source identity
- keep same job from different sources as separate rows/cards
- optionally add a future lightweight “possible duplicate” marker, but do not merge by default

Dedup order:

1. exact match on (source_feed_id, external_id)
2. optional fallback on normalized source_url for sources with unstable IDs
3. stop there

Do not do cross-source semantic dedup in v1.
Do not use embeddings in default ingestion.
Do not merge jobs across sources if the product wants separate cards.

## LLM / Cost Policy

Use near-zero AI in ingestion.

Policy:

- no LLM extraction during normal scans
- no embeddings for every row
- no semantic dedup in the hot path
- only use AI later for:
  - agent workflows
  - premium enrichment
  - user-triggered “summarize/extract”
  - small backfills for selected sources

For large-volume sources, rely on:

- deterministic field mapping
- source-specific parsers
- exact source dedup
  This is the lowest-cost architecture that still scales to thousands of jobs.

## Source Onboarding

- source metadata in sources
- one source_feed config
- one adapter module for fetch/pagination/auth/parsing
- one mapping function into the shared base row
- one card renderer or reuse of an existing card_type

A new source should not require:

- a DB migration for custom fields
- a new table by default
- LLM parsing logic
- cross-source normalization work unless later needed

## Test Plan

Test these scenarios:

- same source item fetched twice
  only one jobs row is kept and last_seen_at updates
- same job appears on two different sources
  two separate rows/cards are kept
- RSS source with sparse fields
  row still stores correctly with null shared fields and populated raw_payload
- JSON API source with many extra fields
  extras are preserved in raw_payload and displayed by its card
- source response shape changes
  parser failure is logged per source/feed and pipeline continues for other items
- high-volume ingestion
  thousands of rows ingest without any LLM or embedding calls
- jobs page
  basic filters still work on shared fields like source, text, and date

## Assumptions

- Main product goal is source-based browsing, not a deeply unified job search engine
- Separate cards for the same job across different sources are acceptable
- Cross-source dedup is intentionally weak in v1
- Basic filtering is enough for now
- PostgreSQL remains the primary storage
- Source-specific payloads are the source of truth for rich card rendering
