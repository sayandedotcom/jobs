import json
from datetime import datetime, timedelta, UTC

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from core.config import settings
from core.database import get_pool
from core.utils import cuid
from pipeline.source_configs import get_source_config
from pipeline.sources.registry import get_source
from pipeline.sources.utils import cosine_similarity

STALE_THRESHOLD_HOURS = 2

SIMILARITY_THRESHOLD = 0.92

PLAN_AGENT_LIMITS: dict[str, int] = {
    "free": 0,
    "pro": 5,
    "enterprise": -1,
}

MATCH_PROMPT = """You are a job matching assistant. Given a raw post from a job board and a candidate's profile, score how well the post matches the candidate.

Candidate Profile:
- Job Title: {job_title}
- Skills: {skills}
- Location: {location}
- Open to Relocate: {open_to_relocate}
- Experience Level: {experience_level}
- Salary Range: {salary_min}-{salary_max}
- Preferred Job Type: {job_type}

Raw Post Content:
{raw_content}

Respond with ONLY a JSON object:
{{
  "relevance_score": <float between 0 and 1>,
  "match_reason": "<1-2 sentence explanation>"
}}"""


async def run_agent_pipeline(agent: dict, run_id: str) -> dict:
    pool = await get_pool()

    skills = (
        agent["skills"]
        if isinstance(agent["skills"], list)
        else json.loads(agent["skills"] or "[]")
    )
    sources = (
        agent["sources"]
        if isinstance(agent["sources"], list)
        else json.loads(agent["sources"] or "[]")
    )

    last_run = await pool.fetchrow(
        """SELECT "startedAt" FROM agent_runs WHERE "agentId" = $1 AND status = 'completed' ORDER BY "startedAt" DESC LIMIT 1""",
        agent["id"],
    )
    since = last_run["startedAt"] if last_run else None

    pool_listing_ids, fetched_listing_ids = [], []
    posts_scanned = 0

    if since is not None:
        pool_listing_ids = await _query_existing_listings(since)
        posts_scanned = len(pool_listing_ids)

    stale_sources = await _get_stale_sources(sources)
    if stale_sources:
        raw_posts = []
        for source_name in stale_sources:
            posts = await _fetch_for_source(source_name, agent)
            raw_posts.extend(posts)

        if raw_posts:
            filtered = _filter_posts(raw_posts, skills, agent["jobTitle"])
            deduped = await _dedup_posts(filtered)
            fetched_listing_ids = await _store_listings(
                deduped, stale_sources[0] if stale_sources else "reddit"
            )
            posts_scanned += len(raw_posts)

    all_listing_ids = list(
        {lid for lid in pool_listing_ids + fetched_listing_ids if lid}
    )

    already_matched = {
        r["listingId"]
        for r in await pool.fetch(
            """SELECT "listingId" FROM agent_results WHERE "agentId" = $1""",
            agent["id"],
        )
    }
    new_listing_ids = [lid for lid in all_listing_ids if lid not in already_matched]

    matched = await _match_listings_to_agent(new_listing_ids, agent, skills)

    jobs_found = len(all_listing_ids)
    new_jobs = 0
    for listing_id, score, reason in matched:
        if score >= 0.5:
            new_jobs += 1
            await pool.execute(
                """INSERT INTO agent_results (id, "agentId", "listingId", "relevanceScore", "matchReason")
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT ("agentId", "listingId") DO NOTHING""",
                cuid(),
                agent["id"],
                listing_id,
                score,
                reason,
            )

    now = datetime.now(UTC)
    interval = agent["scanIntervalMinutes"]
    await pool.execute(
        """UPDATE agent_runs SET status = 'completed', "postsScanned" = $1, "jobsFound" = $2, "newJobs" = $3, "finishedAt" = $4
        WHERE id = $5""",
        posts_scanned,
        jobs_found,
        new_jobs,
        now,
        run_id,
    )

    await pool.execute(
        """UPDATE agents SET "lastRunAt" = $1, "nextRunAt" = $2 WHERE id = $3""",
        now,
        now + timedelta(minutes=interval),
        agent["id"],
    )

    return {
        "postsScanned": posts_scanned,
        "jobsFound": jobs_found,
        "newJobs": new_jobs,
    }


async def _query_existing_listings(since: datetime) -> list[str]:
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT id FROM listings WHERE "createdAt" > $1 ORDER BY "createdAt" DESC""",
        since,
    )
    return [row["id"] for row in rows]


async def _get_stale_sources(sources: list[str]) -> list[str]:
    pool = await get_pool()
    stale = []
    cutoff = datetime.now(UTC) - timedelta(hours=STALE_THRESHOLD_HOURS)
    for source_name in sources:
        last_scan = await pool.fetchrow(
            """SELECT "startedAt" FROM scan_runs WHERE "sourceName" = $1 AND status = 'completed' ORDER BY "startedAt" DESC LIMIT 1""",
            source_name,
        )
        if not last_scan or last_scan["startedAt"] < cutoff:
            stale.append(source_name)
    return stale


async def _fetch_for_source(source_name: str, agent: dict) -> list[dict]:
    pool = await get_pool()

    config = get_source_config(source_name)
    source = get_source(source_name, **config)
    if not source:
        return []

    rows = await pool.fetch(
        """SELECT name, type FROM sub_sources WHERE "sourceId" = (SELECT id FROM sources WHERE name = $1)""",
        source_name,
    )
    sub_sources = [{"name": row["name"], "type": row["type"]} for row in rows]
    if not sub_sources:
        return []

    last_run = await pool.fetchrow(
        """SELECT "startedAt" FROM agent_runs WHERE "agentId" = $1 AND status = 'completed' ORDER BY "startedAt" DESC LIMIT 1""",
        agent["id"],
    )
    since = last_run["startedAt"] if last_run else None

    try:
        return await source.fetch_new_posts(sub_sources, since)
    except Exception:
        return []


def _filter_posts(posts: list[dict], skills: list[str], job_title: str) -> list[dict]:
    keywords = set(kw.lower() for kw in skills)
    keywords.add(job_title.lower())
    base_kw = [
        "hiring",
        "job",
        "position",
        "opening",
        "looking for",
        "seeking",
        "recruiting",
        "remote",
        "full-time",
        "part-time",
        "contract",
        "opportunity",
        "career",
        "vacancy",
        "role",
        "[hiring]",
        "[for hire]",
    ]
    keywords.update(base_kw)

    filtered = []
    for post in posts:
        content_lower = post["raw_content"].lower()
        if any(kw in content_lower for kw in keywords):
            filtered.append(post)
    return filtered


async def _dedup_posts(posts: list[dict]) -> list[dict]:
    if not posts:
        return posts

    pool = await get_pool()
    deduped = []

    for post in posts:
        existing = await pool.fetchrow(
            """SELECT id, "listingId" FROM raw_posts WHERE "externalId" = $1""",
            post["external_id"],
        )
        if existing:
            continue
        deduped.append(post)

    if not deduped:
        return deduped

    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.GEMINI_API_KEY,
    )

    existing_rows = await pool.fetch(
        """SELECT id, "embeddingText" FROM listings WHERE "createdAt" > NOW() - INTERVAL '30 days'"""
    )
    existing_embeddings = []
    if existing_rows:
        texts = [r["embeddingText"] or "" for r in existing_rows]
        existing_embeddings = await embeddings_model.aembed_documents(texts)

    unique = []
    for post in deduped:
        embed_text = post["raw_content"][:500]
        if not existing_rows:
            unique.append(post)
            continue

        new_embedding = await embeddings_model.aembed_query(embed_text)
        is_dup = False
        for i, _row in enumerate(existing_rows):
            if i < len(existing_embeddings):
                score = cosine_similarity(new_embedding, existing_embeddings[i])
                if score >= SIMILARITY_THRESHOLD:
                    is_dup = True
                    break
        if not is_dup:
            unique.append(post)

    return unique


async def _store_listings(posts: list[dict], source_name: str) -> list[str]:
    if not posts:
        return []

    pool = await get_pool()
    source_row = await pool.fetchrow(
        "SELECT id FROM sources WHERE name = $1", source_name
    )
    if not source_row:
        return []

    source_id = source_row["id"]
    listing_ids = []

    for post in posts:
        existing = await pool.fetchrow(
            """SELECT id, "listingId" FROM raw_posts WHERE "externalId" = $1""",
            post["external_id"],
        )
        if existing:
            if existing["listingId"]:
                listing_ids.append(existing["listingId"])
            continue

        embed_text = post["raw_content"][:500]
        title = post["raw_content"].split("\n", 1)[0].strip()
        if title.startswith("Title:"):
            title = title[len("Title:") :].strip()
        if len(title) > 150:
            title = title[:147] + "..."
        title = title or "Untitled"

        listing_row = await pool.fetchrow(
            """INSERT INTO listings (id, title, company, description, location, salary, url, "jobType", "applyUrl", "postedAt", "embeddingText", "sourceName", metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT DO NOTHING
            RETURNING id""",
            cuid(),
            title,
            post.get("author") or "Unknown",
            post["raw_content"],
            None,
            None,
            post.get("permalink"),
            None,
            None,
            None,
            embed_text,
            source_name,
            json.dumps(post.get("metadata", {})),
        )
        if listing_row:
            listing_id = listing_row["id"]
            listing_ids.append(listing_id)
            posted_at = None
            if post.get("posted_at"):
                try:
                    posted_at = datetime.fromisoformat(post["posted_at"])
                except (ValueError, TypeError):
                    posted_at = None
            await pool.execute(
                """INSERT INTO raw_posts (id, "sourceId", "externalId", "rawContent", permalink, author, "postedAt", processed, "listingId")
                VALUES ($1, $2, $3, $4, $5, $6, $7, true, $8)""",
                cuid(),
                source_id,
                post["external_id"],
                post["raw_content"],
                post.get("permalink"),
                post.get("author"),
                posted_at,
                listing_id,
            )

    return listing_ids


async def _match_listings_to_agent(
    listing_ids: list[str], agent: dict, skills: list[str]
) -> list[tuple[str, float, str]]:
    if not listing_ids:
        return []

    pool = await get_pool()
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0,
    )

    matched = []
    for listing_id in listing_ids:
        listing = await pool.fetchrow(
            "SELECT * FROM listings WHERE id = $1", listing_id
        )
        if not listing:
            continue

        try:
            prompt = MATCH_PROMPT.format(
                job_title=agent["jobTitle"],
                skills=", ".join(skills),
                location=agent.get("location") or "Any",
                open_to_relocate=str(agent.get("openToRelocate", False)),
                experience_level=agent.get("experienceLevel") or "Any",
                salary_min=agent.get("salaryMin") or "Any",
                salary_max=agent.get("salaryMax") or "Any",
                job_type=agent.get("jobType") or "Any",
                raw_content=listing["description"][:2000],
            )
            message = HumanMessage(content=prompt)
            response = await llm.ainvoke([message])
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            score = float(data.get("relevance_score", 0))
            reason = data.get("match_reason", "")
            matched.append((listing_id, score, reason))
        except Exception:
            matched.append((listing_id, 0.5, "Auto-matched"))

    return matched
