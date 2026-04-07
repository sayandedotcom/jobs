import json
from datetime import datetime, timedelta, UTC

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from core.config import settings
from core.database import get_pool
from pipeline.source_configs import get_source_config
from pipeline.sources.registry import get_source

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
        "SELECT started_at FROM agent_runs WHERE agent_id = $1 AND status = 'completed' ORDER BY started_at DESC LIMIT 1",
        agent["id"],
    )
    since = last_run["started_at"] if last_run else None

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
            filtered = _filter_posts(raw_posts, skills, agent["job_title"])
            deduped = await _dedup_posts(filtered)
            fetched_listing_ids = await _store_listings(
                deduped, stale_sources[0] if stale_sources else "reddit"
            )
            posts_scanned += len(raw_posts)

    all_listing_ids = list(
        {lid for lid in pool_listing_ids + fetched_listing_ids if lid}
    )

    already_matched = {
        r["listing_id"]
        for r in await pool.fetch(
            "SELECT listing_id FROM agent_results WHERE agent_id = $1",
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
                """INSERT INTO agent_results (agent_id, listing_id, relevance_score, match_reason)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (agent_id, listing_id) DO NOTHING""",
                agent["id"],
                listing_id,
                score,
                reason,
            )

    now = datetime.now(UTC)
    interval = agent["scan_interval_minutes"]
    await pool.execute(
        """UPDATE agent_runs SET status = 'completed', posts_scanned = $1, jobs_found = $2, new_jobs = $3, finished_at = $4
        WHERE id = $5""",
        posts_scanned,
        jobs_found,
        new_jobs,
        now,
        run_id,
    )

    await pool.execute(
        """UPDATE agents SET last_run_at = $1, next_run_at = $2 WHERE id = $3""",
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
        "SELECT id FROM listings WHERE created_at > $1 ORDER BY created_at DESC",
        since,
    )
    return [row["id"] for row in rows]


async def _get_stale_sources(sources: list[str]) -> list[str]:
    pool = await get_pool()
    stale = []
    cutoff = datetime.now(UTC) - timedelta(hours=STALE_THRESHOLD_HOURS)
    for source_name in sources:
        last_scan = await pool.fetchrow(
            "SELECT started_at FROM scan_runs WHERE source_name = $1 AND status = 'completed' ORDER BY started_at DESC LIMIT 1",
            source_name,
        )
        if not last_scan or last_scan["started_at"] < cutoff:
            stale.append(source_name)
    return stale


async def _fetch_for_source(source_name: str, agent: dict) -> list[dict]:
    pool = await get_pool()

    config = get_source_config(source_name)
    source = get_source(source_name, **config)
    if not source:
        return []

    rows = await pool.fetch(
        "SELECT name, type FROM sub_sources WHERE source_id = (SELECT id FROM sources WHERE name = $1)",
        source_name,
    )
    sub_sources = [{"name": row["name"], "type": row["type"]} for row in rows]
    if not sub_sources:
        return []

    last_run = await pool.fetchrow(
        "SELECT started_at FROM agent_runs WHERE agent_id = $1 AND status = 'completed' ORDER BY started_at DESC LIMIT 1",
        agent["id"],
    )
    since = last_run["started_at"] if last_run else None

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
    """Two-stage dedup: exact external_id check + embedding cosine similarity."""
    if not posts:
        return posts

    pool = await get_pool()
    deduped = []

    for post in posts:
        existing = await pool.fetchrow(
            "SELECT id, listing_id FROM raw_posts WHERE external_id = $1",
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
        "SELECT id, embedding_text FROM listings WHERE created_at > NOW() - INTERVAL '30 days'"
    )
    existing_embeddings = []
    if existing_rows:
        texts = [r["embedding_text"] or "" for r in existing_rows]
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
                score = _cosine_similarity(new_embedding, existing_embeddings[i])
                if score >= SIMILARITY_THRESHOLD:
                    is_dup = True
                    break
        if not is_dup:
            unique.append(post)

    return unique


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


async def _store_listings(posts: list[dict], source_name: str) -> list[str]:
    """Persist posts to listings + raw_posts tables, return new listing IDs."""
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
            "SELECT id, listing_id FROM raw_posts WHERE external_id = $1",
            post["external_id"],
        )
        if existing:
            if existing["listing_id"]:
                listing_ids.append(existing["listing_id"])
            continue

        embed_text = post["raw_content"][:500]
        title = post["raw_content"].split("\n", 1)[0].strip()
        if title.startswith("Title:"):
            title = title[len("Title:") :].strip()
        if len(title) > 150:
            title = title[:147] + "..."
        title = title or "Untitled"

        listing_row = await pool.fetchrow(
            """INSERT INTO listings (title, company, description, location, salary, url, job_type, apply_url, posted_at, embedding_text, source_name, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT DO NOTHING
            RETURNING id""",
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
                """INSERT INTO raw_posts (source_id, external_id, raw_content, permalink, author, posted_at, processed, listing_id)
                VALUES ($1, $2, $3, $4, $5, $6, true, $7)""",
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
                job_title=agent["job_title"],
                skills=", ".join(skills),
                location=agent.get("location") or "Any",
                open_to_relocate=str(agent.get("open_to_relocate", False)),
                experience_level=agent.get("experience_level") or "Any",
                salary_min=agent.get("salary_min") or "Any",
                salary_max=agent.get("salary_max") or "Any",
                job_type=agent.get("job_type") or "Any",
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
