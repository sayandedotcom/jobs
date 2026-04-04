import json
from datetime import datetime, UTC

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from core.config import settings
from core.database import get_pool


MATCH_PROMPT = """You are a job matching assistant. Given a job listing and a candidate's profile, score how well the job matches the candidate.

Candidate Profile:
- Job Title: {job_title}
- Skills: {skills}
- Location: {location}
- Open to Relocate: {open_to_relocate}
- Experience Level: {experience_level}
- Salary Range: {salary_min}-{salary_max}
- Preferred Job Type: {job_type}

Job Listing:
- Title: {listing_title}
- Company: {listing_company}
- Description: {listing_description}
- Location: {listing_location}
- Salary: {listing_salary}
- Job Type: {listing_job_type}

Respond with ONLY a JSON object:
{{
  "relevance_score": <float between 0 and 1>,
  "match_reason": "<1-2 sentence explanation of why this job matches or doesn't match>"
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

    raw_posts = []
    for source_name in sources:
        posts = await _fetch_for_source(source_name, agent)
        raw_posts.extend(posts)

    filtered = _filter_posts(raw_posts, skills, agent["job_title"])
    extracted_jobs = await _extract_jobs(filtered)

    new_listing_ids = await _store_listings(
        extracted_jobs, sources[0] if sources else "reddit"
    )
    matched = await _match_listings_to_agent(new_listing_ids, agent, skills)

    jobs_found = len(new_listing_ids)
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
        len(raw_posts),
        jobs_found,
        new_jobs,
        now,
        run_id,
    )

    await pool.execute(
        """UPDATE agents SET last_run_at = $1, next_run_at = $2 WHERE id = $3""",
        now,
        now.__class__.utcnow() + __import__("datetime").timedelta(minutes=interval),
        agent["id"],
    )

    return {
        "postsScanned": len(raw_posts),
        "jobsFound": jobs_found,
        "newJobs": new_jobs,
    }


async def _fetch_for_source(source_name: str, agent: dict) -> list[dict]:
    pool = await get_pool()

    if source_name == "reddit":
        from pipeline.sources.reddit import RedditSource

        source = RedditSource(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )
    else:
        return []

    rows = await pool.fetch(
        "SELECT name FROM sub_sources WHERE source_id = (SELECT id FROM sources WHERE name = $1) AND is_active = true",
        source_name,
    )
    subreddits = [row["name"] for row in rows]
    if not subreddits:
        return []

    last_run = await pool.fetchrow(
        "SELECT started_at FROM agent_runs WHERE agent_id = $1 AND status = 'completed' ORDER BY started_at DESC LIMIT 1",
        agent["id"],
    )
    since = last_run["started_at"] if last_run else None

    try:
        return await source.fetch_new_posts(subreddits, since)
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


async def _extract_jobs(posts: list[dict]) -> list[tuple[dict, dict]]:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0,
    )

    extraction_prompt = """You are a job posting extraction assistant. Given a Reddit post, extract structured job information.

If the post is NOT a job posting, set is_job_posting to false.

For valid job postings, extract:
- title: The job title
- company: The company name (use "Not specified" if not mentioned)
- description: A clean summary (2-3 paragraphs)
- location: Location or "Remote" if remote (null if not mentioned)
- salary: Salary range if mentioned (null if not)
- job_type: One of "full-time", "part-time", "contract", "freelance", "internship" (null if unclear)
- apply_url: Application URL if provided (null if not)
- is_job_posting: true if this is a job posting, false otherwise

Respond with ONLY a JSON object:

Post content:
{content}"""

    extracted = []
    for post in posts:
        try:
            message = HumanMessage(
                content=extraction_prompt.format(content=post["raw_content"])
            )
            response = await llm.ainvoke([message])
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            if data.get("is_job_posting") and data.get("title"):
                job = {
                    "title": data.get("title", ""),
                    "company": data.get("company", "Not specified"),
                    "description": data.get("description", ""),
                    "location": data.get("location"),
                    "salary": data.get("salary"),
                    "job_type": data.get("job_type"),
                    "apply_url": data.get("apply_url"),
                }
                extracted.append((post, job))
        except Exception:
            continue
    return extracted


async def _store_listings(jobs: list[tuple[dict, dict]], source_name: str) -> list[str]:
    if not jobs:
        return []

    pool = await get_pool()
    source_row = await pool.fetchrow(
        "SELECT id FROM sources WHERE name = $1", source_name
    )
    if not source_row:
        return []

    source_id = source_row["id"]
    listing_ids = []

    for post, job in jobs:
        existing = await pool.fetchrow(
            "SELECT id FROM raw_posts WHERE external_id = $1",
            post["external_id"],
        )
        if existing:
            if existing["listing_id"]:
                listing_ids.append(existing["listing_id"])
            continue

        embed_text = f"{job['title']} {job['company']} {job.get('location', '')}"
        listing_row = await pool.fetchrow(
            """INSERT INTO listings (title, company, description, location, salary, url, job_type, apply_url, posted_at, embedding_text)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT DO NOTHING
            RETURNING id""",
            job["title"],
            job["company"],
            job["description"],
            job.get("location"),
            job.get("salary"),
            post.get("permalink"),
            job.get("job_type"),
            job.get("apply_url"),
            None,
            embed_text,
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
                listing_title=listing["title"],
                listing_company=listing["company"],
                listing_description=listing["description"][:1000],
                listing_location=listing.get("location") or "Not specified",
                listing_salary=listing.get("salary") or "Not specified",
                listing_job_type=listing.get("job_type") or "Not specified",
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
