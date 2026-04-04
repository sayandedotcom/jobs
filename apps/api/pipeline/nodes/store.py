from datetime import datetime, UTC

from core.database import get_pool
from pipeline.state import PipelineState


async def store_node(state: PipelineState) -> dict:
    pool = await get_pool()
    jobs_added = 0

    source_row = await pool.fetchrow(
        "SELECT id FROM sources WHERE name = $1", state["source_name"]
    )
    if not source_row:
        return {"jobs_added": 0, "errors": state["errors"] + 1}
    source_id = source_row["id"]

    for item in state["new_listings"]:
        post = item["post"]
        job = item["job"]
        posted_at = None
        if post.get("posted_at"):
            try:
                posted_at = datetime.fromisoformat(post["posted_at"])
            except (ValueError, TypeError):
                posted_at = None

        listing_row = await pool.fetchrow(
            """INSERT INTO listings (title, company, description, location, salary, url, job_type, apply_url, posted_at, embedding_text)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id""",
            job["title"],
            job["company"],
            job["description"],
            job.get("location"),
            job.get("salary"),
            post.get("permalink"),
            job.get("job_type"),
            job.get("apply_url"),
            posted_at,
            item["embedding_text"],
        )
        listing_id = listing_row["id"]
        jobs_added += 1

        await pool.execute(
            """INSERT INTO raw_posts (source_id, external_id, raw_content, permalink, author, posted_at, processed, listing_id)
            VALUES ($1, $2, $3, $4, $5, $6, true, $7)
            ON CONFLICT (source_id, external_id) DO UPDATE SET processed = true, listing_id = $7""",
            source_id,
            post["external_id"],
            post["raw_content"],
            post.get("permalink"),
            post.get("author"),
            posted_at,
            listing_id,
        )

    for external_id, listing_id in state["matched_listings"]:
        await pool.execute(
            """INSERT INTO raw_posts (source_id, external_id, raw_content, permalink, author, posted_at, processed, listing_id)
            VALUES ($1, $2, $3, $4, $5, $6, true, $7)
            ON CONFLICT (source_id, external_id) DO UPDATE SET processed = true, listing_id = $7""",
            source_id,
            external_id,
            "",
            None,
            None,
            None,
            listing_id,
        )

    now = datetime.now(UTC)
    await pool.execute(
        """UPDATE scan_runs SET status = 'completed', posts_found = $1, posts_new = $2, jobs_added = $3, errors = $4, finished_at = $5
        WHERE id = $6""",
        state["posts_found"],
        state["posts_new"],
        jobs_added,
        state["errors"],
        now,
        state["scan_run_id"],
    )

    return {"jobs_added": jobs_added}
