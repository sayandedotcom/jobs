# Job Sources Master List

All job sources researched for this platform, organized by tier (implementation priority)
and category. Every source mentioned across research is listed here.

---

## Tier 1 — ATS Platforms (Public Job Board APIs)

Structured JSON, no scraping, no auth (mostly). Each company has a unique slug/board_token.
Maintain a slug registry in `sub_sources` table.

| #   | Source              | API Endpoint Pattern                                                         | Auth        | Difficulty | Notes                                                                                                              |
| --- | ------------------- | ---------------------------------------------------------------------------- | ----------- | ---------- | ------------------------------------------------------------------------------------------------------------------ |
| 1   | **Greenhouse** ✅   | `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true` | No          | LOW        | Thousands of companies (Stripe, Cloudflare, etc.). Structured JSON with title, location, departments, description. |
| 2   | **Lever** ✅        | `https://api.lever.co/v0/postings/{company_slug}?mode=json`                  | No          | LOW        | Major ATS. Netflix, Quora, etc. Structured job data.                                                               |
| 3   | **AshbyHQ** ✅      | `https://api.ashbyhq.com/posting-api/{company_slug}`                         | No          | LOW        | Growing ATS popular with startups. Public posting API.                                                             |
| 4   | **Workable** ✅     | `https://www.workable.com/spi/v3/accounts/{subdomain}/jobs?state=published`  | No (public) | LOW        | Public jobs API at `jobs.workable.com/api/v1/jobs`. No auth needed.                                                |
| 5   | **SmartRecruiters** | `https://api.smartrecruiters.com/v1/companies/{company_id}/postings`         | No          | LOW        | Public API with structured job data.                                                                               |
| 6   | **Recruitee**       | `https://{company}.recruitee.com/api/offers/`                                | No          | LOW        | Popular in EU.                                                                                                     |
| 7   | **Teamtailor** ✅   | `{company}.teamtailor.com/jobs.rss`                                          | No          | LOW        | Public RSS feed. Popular in Nordics/EU.                                                                            |
| 8   | **Breezy HR**       | Scrape public job board pages                                                | No          | MEDIUM     | Smaller ATS.                                                                                                       |
| 9   | **Jobvite**         | `https://app.jobvite.com/Company/{company_slug}`                             | Partial     | MEDIUM     | Used by many mid-size companies.                                                                                   |
| 10  | **Workday**         | RSS feeds per company                                                        | No          | MEDIUM     | Enterprise ATS — Amazon, NVIDIA use it. RSS available.                                                             |
| 11  | **Taleo/Oracle**    | RSS/scrape                                                                   | No          | HIGH       | Enterprise, used by Fortune 500.                                                                                   |
| 12  | **iCIMS**           | Scrape public job pages                                                      | No          | HIGH       | Enterprise ATS.                                                                                                    |

### Pre-configured Company Slugs (from career-ops reference)

**Ashby:** Anthropic, Retool, n8n, Lindy, Arize AI, PolyAI, Parloa, Hume AI,
Deepgram, Vapi, Bland AI, Decagon, Langfuse, Cognigy, Speechmatics

**Greenhouse:** OpenAI, Mistral, Cohere, LangChain, Pinecone, Airtable, Vercel,
Temporal, Glean, ElevenLabs, Sierra, Talkdesk, Genesys, Salesforce, Twilio, Gong,
Dialpad, Weights & Biases, Factorial, Attio, Tinybird, Clarity AI, Travelperk

**Lever:** Salesforce, PolyAI, LivePerson, etc.

---

## Tier 2 — Social & Community Platforms

| #   | Source                             | Method                                                                                                | Auth                | Difficulty | Notes                                                                                                                                            |
| --- | ---------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 13  | **Reddit** ✅                      | PRAW API                                                                                              | Yes (OAuth)         | LOW        | Implemented.                                                                                                                                     |
| 14  | **Hacker News "Who is Hiring"** ✅ | Algolia API: `https://hn.algolia.com/api/v1/search?query=&tags=story` filter "Ask HN: Who is hiring?" | No                  | MEDIUM     | Implemented. Monthly thread with 500-800+ job posts. Free, no auth. Unstructured free-text comments — need LLM extraction.                       |
| 15  | **Twitter/X**                      | X API v2 (search tweets)                                                                              | Yes ($100/mo Basic) | HIGH       | Search "hiring", "job opening", "we're hiring". Noisy results, lots of spam. Rate limited: 60 req/15 min. Or scrape via Nitter/RSS (unreliable). |
| 16  | **Blind** (TeamBlind)              | Scrape                                                                                                | No                  | HIGH       | Popular for tech workers discussing jobs. Anti-bot.                                                                                              |
| 17  | **Discord job servers**            | Bot/Discord API                                                                                       | Yes (Bot token)     | MEDIUM     | Many tech communities have job posting channels.                                                                                                 |

---

## Tier 3 — Aggregator Job Boards (API or RSS)

| #   | Source                                | URL                                                    | Method                                                                                       | Auth                | Difficulty   | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --- | ------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 18  | **WeWorkRemotely** ✅                 | https://weworkremotely.com                             | `https://weworkremotely.com/api/v1/remote-jobs` (Bearer token)                               | Yes (partner token) | MEDIUM (API) | One of the largest remote job boards. Authenticated JSON API, 1,000 req/day. Email api@weworkremotely.com for token. Structured fields: id, company, title, region, salary_range, category_id.                                                                                                                                                                                                                                         |
| 19  | **RemoteOK** ✅                       | https://remoteok.com                                   | `https://remoteok.com/api`                                                                   | No                  | LOW          | Free public JSON API. Excellent for remote jobs. Single GET returns all jobs.                                                                                                                                                                                                                                                                                                                                                          |
| 20  | **Remotive** ✅                       | https://remotive.com                                   | `https://remotive.com/api/remote-jobs`                                                       | No                  | LOW          | Free public JSON API.                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 21  | **JobsCollider / RemoteFirstJobs** ✅ | https://remotefirstjobs.com / https://jobscollider.com | `GET https://remotefirstjobs.com/api/search-jobs?category={category}`                        | No                  | LOW          | **8,000+ jobs across 16 categories.** Updated every 10 min. Up to 500 jobs/category (5 pages x 100). 24hr delay. Must credit source. Structured JSON with title, company, salary, seniority, locations, description (HTML). Categories: software_development, cybersecurity, customer_service, design, marketing, sales, product, business, data, devops, finance_legal, human_resources, qa, writing, project_management, all_others. |
| 22  | **Arbeitnow**                         | https://www.arbeitnow.com                              | `https://www.arbeitnow.com/api/job-board-api`                                                | No                  | LOW          | Free public JSON API.                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 23  | **Jobicy**                            | https://jobicy.com                                     | `https://jobicy.com/api/v2/remote-jobs`                                                      | No                  | LOW          | Free public API.                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 24  | **Himalayas** ✅                      | https://himalayas.app                                  | `https://himalayas.app/jobs/api` (browse) / `https://himalayas.app/jobs/api/search` (search) | No                  | LOW          | Remote job board with public JSON API. Browse + search endpoints, max 20/page.                                                                                                                                                                                                                                                                                                                                                         |
| 25  | **Remote.co**                         | https://remote.co                                      | Scrape                                                                                       | No                  | HIGH         | Remote job listings. Anti-bot protection.                                                                                                                                                                                                                                                                                                                                                                                              |
| 26  | **JustRemote**                        | https://justremote.co                                  | Scrape                                                                                       | No                  | HIGH         | Remote jobs.                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 27  | **Jobspresso**                        | https://jobspresso.co                                  | Scrape                                                                                       | No                  | MEDIUM       | Curated remote jobs.                                                                                                                                                                                                                                                                                                                                                                                                                   |
| 28  | **Working Nomads**                    | https://workingnomads.co                               | Scrape/RSS                                                                                   | No                  | LOW (RSS)    | Remote job board with RSS feeds.                                                                                                                                                                                                                                                                                                                                                                                                       |
| 29  | **NoDesk**                            | https://nodesk.co                                      | Scrape                                                                                       | No                  | MEDIUM       | Remote jobs.                                                                                                                                                                                                                                                                                                                                                                                                                           |
| 30  | **EU Remote Jobs**                    | https://euremotejobs.com                               | Scrape                                                                                       | No                  | MEDIUM       | EU-focused remote.                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 31  | **4 Day Week**                        | https://4dayweek.io                                    | Scrape/API                                                                                   | No                  | MEDIUM       | Jobs with 4-day work weeks.                                                                                                                                                                                                                                                                                                                                                                                                            |
| 32  | **Turing**                            | https://turing.com                                     | Scrape                                                                                       | No                  | HIGH         | Remote developer jobs.                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 33  | **RemoteWLB**                         | https://www.remotewlb.com                              | Scrape / GitHub open data (`RemoteWLB/remote-jobs`)                                          | No                  | LOW (data)   | Aggregates 200K+ jobs from 8K+ companies. Open source data on GitHub.                                                                                                                                                                                                                                                                                                                                                                  |
| 34  | **Remote Hunt**                       | https://remotehunt.com                                 | Scrape                                                                                       | No                  | MEDIUM       | Remote job board.                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 35  | **Workew**                            | https://workew.com                                     | Scrape                                                                                       | No                  | MEDIUM       | Remote job board.                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 36  | **WantRemote**                        | https://wantremote.com                                 | Scrape                                                                                       | No                  | MEDIUM       | Remote job board.                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 37  | **Remoters**                          | https://remoters.net                                   | Scrape                                                                                       | No                  | MEDIUM       | Remote job board.                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 38  | **JSRemotely**                        | https://jsremotely.com                                 | Scrape                                                                                       | No                  | MEDIUM       | JavaScript remote jobs.                                                                                                                                                                                                                                                                                                                                                                                                                |
| 39  | **Remote4Me**                         | https://remote4me.com                                  | Scrape                                                                                       | No                  | MEDIUM       | Remote job aggregator.                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 40  | **RemoteGlobal**                      | https://remoteglobal.com                               | Scrape                                                                                       | No                  | MEDIUM       | Remote jobs.                                                                                                                                                                                                                                                                                                                                                                                                                           |

---

## Tier 4 — Startup & Niche Job Boards

| #   | Source                             | URL                                      | Method        | Auth | Difficulty | Notes                                                                      |
| --- | ---------------------------------- | ---------------------------------------- | ------------- | ---- | ---------- | -------------------------------------------------------------------------- |
| 41  | **Wellfound** (AngelList)          | https://angel.co / https://wellfound.com | Scrape        | No   | HIGH       | Startup jobs. No public API. Heavy JS-rendered SPA, anti-bot (Cloudflare). |
| 42  | **Otta**                           | https://otta.com                         | Scrape        | No   | HIGH       | Tech-focused job board. React-heavy SPA. Needs headless browser.           |
| 43  | **Y Combinator Work at a Startup** | https://www.workatastartup.com           | API or scrape | No   | MEDIUM     | YC-backed startup jobs.                                                    |
| 44  | **ProductHunt Jobs**               | https://www.producthunt.com/jobs         | Scrape        | No   | MEDIUM     | Tech/startup jobs.                                                         |
| 45  | **Dynamite Jobs**                  | https://dynamitejobs.com                 | Scrape        | No   | MEDIUM     | Remote jobs from Dynamo Ventures portfolio companies.                      |
| 46  | **Epic Jobs**                      | https://epicjobs.co                      | Scrape        | No   | MEDIUM     | Curated jobs.                                                              |
| 47  | **DevSnap**                        | https://devsnap.io                       | Scrape        | No   | MEDIUM     | Developer jobs.                                                            |
| 48  | **JobBoardSearch**                 | https://jobboardsearch.com               | Scrape        | No   | MEDIUM     | Meta job board search.                                                     |

---

## Tier 5 — Specialized/Niche Job Boards

| #   | Source                           | Method     | Difficulty | Notes                                            |
| --- | -------------------------------- | ---------- | ---------- | ------------------------------------------------ |
| 49  | **Authentic Jobs**               | Scrape/RSS | LOW (RSS)  | Design/dev focused.                              |
| 50  | **Smashing Jobs**                | Scrape/RSS | LOW (RSS)  | Design/dev jobs by Smashing Magazine.            |
| 51  | **Dribbble Jobs**                | Scrape     | HIGH       | Design jobs. Requires auth. Lazy-loaded content. |
| 52  | **Behance Jobs**                 | Scrape     | HIGH       | Creative/design jobs.                            |
| 53  | **Key Values** (keyvalues.com)   | Scrape     | MEDIUM     | Culture-focused job search.                      |
| 54  | **Functional Jobs**              | Scrape     | MEDIUM     | Functional programming jobs.                     |
| 55  | **Ruby Now**                     | Scrape     | MEDIUM     | Ruby jobs.                                       |
| 56  | **Python.org Jobs**              | Scrape     | MEDIUM     | Python jobs board.                               |
| 57  | **Golang Jobs** (golangjobs.com) | Scrape     | MEDIUM     | Go jobs.                                         |
| 58  | **Rust Jobs** (rustjobs.dev)     | Scrape     | MEDIUM     | Rust-specific jobs.                              |
| 59  | **React.js Jobs**                | Scrape     | MEDIUM     | React-focused.                                   |
| 60  | **Vue.js Jobs**                  | Scrape     | MEDIUM     | Vue-focused.                                     |
| 61  | **Crypto Jobs List**             | API (paid) | MEDIUM     | Blockchain/crypto jobs.                          |
| 62  | **Web3 Jobs**                    | Scrape     | MEDIUM     | Web3/blockchain.                                 |

---

## Tier 6 — Freelance & Contract Platforms

| #   | Source         | URL                    | Method      | Auth    | Difficulty | Notes                         |
| --- | -------------- | ---------------------- | ----------- | ------- | ---------- | ----------------------------- |
| 63  | **Upwork**     | https://upwork.com     | GraphQL API | Yes     | HIGH       | Freelance jobs. Rate limited. |
| 64  | **Toptal**     | https://toptal.com     | Scrape      | No      | HIGH       | Freelance/contract elite.     |
| 65  | **Contra**     | https://contra.com     | Scrape      | No      | MEDIUM     | Freelance, no commission.     |
| 66  | **Braintrust** | https://braintrust.dev | Scrape/API  | Partial | MEDIUM     | Web3 freelance.               |
| 67  | **Gun.io**     | https://gun.io         | Scrape      | No      | MEDIUM     | Developer freelance.          |

---

## Tier 7 — Major Job Boards (High Difficulty)

| #   | Source            | URL                                        | Method                      | Auth | Difficulty    | Notes                                                                                                                     |
| --- | ----------------- | ------------------------------------------ | --------------------------- | ---- | ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 68  | **Indeed**        | https://indeed.com / https://in.indeed.com | No public API (scrape only) | No   | **VERY HIGH** | Aggressive anti-bot (Cloudflare, CAPTCHAs). Scraping violates ToS. Actively blocks scrapers.                              |
| 69  | **Glassdoor**     | https://glassdoor.com                      | Scrape                      | No   | **VERY HIGH** | Similar to Indeed. Cloudflare + CAPTCHA. Login-walled.                                                                    |
| 70  | **ZipRecruiter**  | https://ziprecruiter.com                   | No public API               | No   | **VERY HIGH** | ToS prohibits scraping.                                                                                                   |
| 71  | **Monster**       | https://monster.com                        | Scrape                      | No   | **VERY HIGH** | Heavy Cloudflare + CAPTCHAs.                                                                                              |
| 72  | **CareerBuilder** | https://careerbuilder.com                  | Scrape                      | No   | **VERY HIGH** | Similar to Monster.                                                                                                       |
| 73  | **LinkedIn**      | https://linkedin.com                       | Login-walled                | Yes  | **EXTREME**   | Aggressive legal action against scrapers. CAPTCHAs, account bans, device fingerprinting. **Excluded from this platform.** |

---

## Tier 8 — Web Search & Discovery APIs (Meta-Sources)

These don't list jobs directly but help discover jobs from across the web.

| #   | Source                            | API Endpoint                                                                | Auth                                       | Difficulty | Notes                                                                                                                                                                                                                                                                                                                                                                     |
| --- | --------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 74  | **SerpAPI — Google Jobs**         | `GET https://serpapi.com/search?engine=google_jobs&q={query}&api_key={key}` | Yes ($50-200/mo)                           | MEDIUM     | **Most powerful meta-source.** Aggregates from LinkedIn, Indeed, ZipRecruiter, Glassdoor, company pages. Structured JSON: title, company_name, location, description, via (source ATS), apply_options, detected_extensions (posted_at, work_from_home, schedule_type). 10 results/page, pagination via next_page_token. Filters: date posted, job type, remote, location. |
| 75  | **Tavily Search**                 | `POST https://api.tavily.com/search`                                        | Yes (free tier: 1K credits/mo, $75/mo Pro) | LOW-MEDIUM | General web search for AI. Good for discovering "we're hiring" blog posts, announcements. Returns cleaned content. Not structured for jobs — needs LLM extraction. Supports: search_depth (basic/advanced), include_raw_content, time_range, include/exclude_domains, country filter.                                                                                     |
| 76  | **Exa**                           | `POST https://api.exa.ai/search`                                            | Yes (pay-per-use, ~$0.007/search)          | LOW-MEDIUM | Neural/embeddings-based semantic search. Great for discovering company career pages and hiring posts. Has `startPublishedDate` for freshness. Returns full page content. Types: neural, auto, fast, deep-lite, deep, deep-reasoning, deep-max, instant. Supports: includeDomains, excludeDomains, category (company, research paper, news, etc.).                         |
| 77  | **JSearch (Adzuna)** via RapidAPI | `https://jsearch.p.rapidapi.com/search`                                     | Yes (RapidAPI key)                         | MEDIUM     | Aggregates from multiple job boards. Free tier available.                                                                                                                                                                                                                                                                                                                 |
| 78  | **Jooble API**                    | Jooble API                                                                  | Yes (free tier)                            | MEDIUM     | Job search engine.                                                                                                                                                                                                                                                                                                                                                        |
| 79  | **Careerjet API**                 | Careerjet Public API                                                        | Yes (affiliate key)                        | MEDIUM     | Job search engine.                                                                                                                                                                                                                                                                                                                                                        |

---

## Tier 9 — Referral Platforms

| #   | Source      | URL                 | Method | Difficulty | Notes                        |
| --- | ----------- | ------------------- | ------ | ---------- | ---------------------------- |
| 80  | **Reffer**  | https://reffer.com  | Scrape | MEDIUM     | Referral-based job platform. |
| 81  | **Reftrac** | https://reftrac.com | Scrape | MEDIUM     | Referral platform.           |
| 82  | **Boon**    | https://getboon.com | Scrape | MEDIUM     | Employee referral platform.  |
| 83  | **Zao**     | https://zao.com     | Scrape | MEDIUM     | Referral hiring platform.    |

---

## Implementation Priority Matrix

### Phase 1 — Immediate (LOW effort, HIGH value, no auth)

| Priority | Source                    | Expected Volume    | Effort                                 |
| -------- | ------------------------- | ------------------ | -------------------------------------- |
| 1        | **JobsCollider API** ✅   | 8,000+ jobs        | Trivial — free JSON API, 16 categories |
| 2        | **Greenhouse** ✅         | High (per company) | Low — build slug registry, fetch JSON  |
| 3        | **Lever** ✅              | High (per company) | Low — same pattern as Greenhouse       |
| 4        | **RemoteOK** ✅           | 1,000+ jobs        | Trivial — single GET request           |
| 5        | **WeWorkRemotely RSS** ✅ | 500+ jobs          | Trivial — parse XML                    |
| 6        | **Remotive** ✅           | 1,000+ jobs        | Trivial — single GET request           |
| 7        | **Arbeitnow**             | 1,000+ jobs        | Trivial — single GET request           |
| 8        | **Jobicy**                | 500+ jobs          | Trivial — single GET request           |
| 9        | **HN Who is Hiring** ✅   | 500-800/mo         | Low — Algolia API + LLM extraction     |
| 10       | **Himalayas** ✅          | 500+ jobs          | Trivial — single GET request           |

### Phase 2 — Medium effort (paid or partial auth)

| Priority | Source                             | Expected Volume    | Effort                                             |
| -------- | ---------------------------------- | ------------------ | -------------------------------------------------- |
| 11       | **SerpAPI Google Jobs**            | 10,000+ jobs       | Medium — paid API, pagination, filter out LinkedIn |
| 12       | **AshbyHQ** ✅                     | High (per company) | Low — public posting API                           |
| 13       | **SmartRecruiters**                | High (per company) | Low — public API                                   |
| 14       | **Workable** ✅                    | Medium             | Low — public jobs API, no auth needed              |
| 15       | **Recruitee**                      | Medium (EU focus)  | Low — public API                                   |
| 16       | **Teamtailor** ✅                  | Medium (Nordics)   | Low — public RSS feed                              |
| 17       | **Y Combinator Work at a Startup** | Medium             | Medium — scrape or API                             |
| 18       | **4 Day Week**                     | Medium             | Medium — niche but popular                         |

### Phase 3 — Higher effort (scraping or expensive APIs)

| Priority | Source                    | Expected Volume | Effort                                    |
| -------- | ------------------------- | --------------- | ----------------------------------------- |
| 19       | **Twitter/X**             | Varies          | High — $100/mo API, noisy data            |
| 20       | **Exa (discovery)**       | Varies          | Medium — semantic search for career pages |
| 21       | **Tavily (discovery)**    | Varies          | Medium — general web discovery            |
| 22       | **Wellfound (AngelList)** | High            | High — SPA, scraping, Cloudflare          |
| 23       | **Dynamite Jobs**         | Medium          | Medium — scrape                           |
| 24       | **Working Nomads RSS**    | Medium          | Low — RSS available                       |

### Phase 4 — Avoid or reconsider

| Source               | Why avoid                                                   |
| -------------------- | ----------------------------------------------------------- |
| **LinkedIn**         | Excluded by design. EXTREME difficulty, legal risk.         |
| **Indeed**           | VERY HIGH difficulty. Cloudflare, CAPTCHAs, ToS violations. |
| **Glassdoor**        | VERY HIGH difficulty. Same as Indeed.                       |
| **ZipRecruiter**     | VERY HIGH difficulty. ToS prohibits scraping.               |
| **Monster**          | VERY HIGH difficulty.                                       |
| **CareerBuilder**    | VERY HIGH difficulty.                                       |
| **Dribbble/Behance** | Requires auth, lazy-loaded, rate limited.                   |

---

## Difficulty Legend

| Difficulty    | Description                                                                                                 |
| ------------- | ----------------------------------------------------------------------------------------------------------- |
| **LOW**       | Free public API or RSS. No auth. Structured JSON/XML. Minimal effort.                                       |
| **MEDIUM**    | Paid API, partial auth, or simple scraping. Some maintenance needed.                                        |
| **HIGH**      | Anti-bot protection, JS rendering, auth walls, or expensive APIs. Requires Playwright or scraping services. |
| **VERY HIGH** | Aggressive anti-bot (Cloudflare + CAPTCHAs), ToS violations, legal risk. Avoid.                             |
| **EXTREME**   | Login-walled, legal action against scrapers, device fingerprinting. Do not attempt.                         |

---

## Key Challenges Across All Sources

### 1. Rate Limiting

- **Greenhouse**: Undocumented, ~100 req/min per IP
- **Lever**: No documented limits, be respectful
- **RemoteOK**: 10 req/minute (free)
- **WWR RSS**: 60 min TTL (their cache)
- **JobsCollider**: 500 jobs/category (5 pages), 24hr delay
- **SerpAPI**: Plan-based (5K-30K searches/mo)
- **X API**: 60 req/15 min for search

### 2. Anti-Bot Protection

Sites using **Cloudflare**, **DataDome**, **PerimeterX**, or **Akamai Bot Manager**:

- Indeed, Glassdoor, Monster, LinkedIn, ZipRecruiter, Wellfound
- Workarounds: rotating proxies, fingerprint spoofing, Playwright — but fragile

### 3. JavaScript-Heavy Sites (SPAs)

Require headless browser (Playwright) — raw `httpx.get()` returns empty:

- Wellfound, Otta, Dribbble, most React/Next.js apps
- Alternative: check Network tab in DevTools for internal JSON APIs

### 4. Duplicate Detection

Same job appears on multiple sources (Greenhouse + Lever + Remotive + SerpAPI).
The `dedup` node is critical — use `external_id` + title/company matching.

### 5. Legal Risks

- Scraping may violate **Terms of Service** (especially LinkedIn, Indeed, Glassdoor)
- Always check `robots.txt` before scraping
- Republishing full descriptions may violate copyright
- GDPR/privacy compliance for personal data

### 6. Data Quality

- **Stale listings** — old jobs still showing
- **Spam/fake listings** — especially on free posting boards
- **Inconsistent formats** — every source structures data differently
- **Missing fields** — salary, job_type often absent

---

## Reference: Career-Ops (github.com/santifer/career-ops)

Not a job source — a personal AI-powered job search tool built on Claude Code.
Useful for:

- **Company slug registry**: 45+ pre-configured companies mapped to ATS (Ashby, Greenhouse, Lever)
- **Validated architecture**: Confirms Greenhouse + Lever + Ashby scanning approach works at scale (740+ jobs evaluated)
- **Portal scanning patterns**: Reference implementation for multi-ATS scanning

GitHub: https://github.com/santifer/career-ops

---

## Reference: JobsCollider Remote Jobs RSS

In addition to the API, JobsCollider also provides RSS feeds:
GitHub: https://github.com/JobsCollider/remote-jobs-rss
