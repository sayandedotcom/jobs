import json
from datetime import datetime, UTC

from core.database import get_pool
from core.utils import cuid
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
        posted_at = None
        if post.get("posted_at"):
            try:
                dt = datetime.fromisoformat(post["posted_at"])
                posted_at = dt.replace(tzinfo=None) if dt.tzinfo else dt
            except (ValueError, TypeError):
                posted_at = None

        listing = _build_listing_payload(state["source_name"], post, item)

        now_ts = datetime.now(UTC).replace(tzinfo=None)
        listing_row = await pool.fetchrow(
            """INSERT INTO listings (id, title, company, description, location, salary, url, "jobType", "applyUrl", "postedAt", "embeddingText", "sourceName", metadata, "createdAt", "updatedAt")
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $14)
            RETURNING id""",
            cuid(),
            listing["title"],
            listing["company"],
            listing["description"],
            listing["location"],
            listing["salary"],
            listing["url"],
            listing["jobType"],
            listing["applyUrl"],
            posted_at,
            listing["embeddingText"],
            state["source_name"],
            json.dumps(listing["metadata"]),
            now_ts,
        )
        listing_id = listing_row["id"]
        jobs_added += 1

        await pool.execute(
            """INSERT INTO raw_posts (id, "sourceId", "externalId", "rawContent", permalink, author, "postedAt", processed, "listingId")
            VALUES ($1, $2, $3, $4, $5, $6, $7, true, $8)
            ON CONFLICT ("sourceId", "externalId") DO UPDATE SET processed = true, "listingId" = $8""",
            cuid(),
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
            """INSERT INTO raw_posts (id, "sourceId", "externalId", "rawContent", permalink, author, "postedAt", processed, "listingId")
            VALUES ($1, $2, $3, $4, $5, $6, $7, true, $8)
            ON CONFLICT ("sourceId", "externalId") DO UPDATE SET processed = true, "listingId" = $8""",
            cuid(),
            source_id,
            external_id,
            "",
            None,
            None,
            None,
            listing_id,
        )

    now = datetime.now(UTC).replace(tzinfo=None)
    await pool.execute(
        """UPDATE scan_runs SET status = 'completed', "postsFound" = $1, "postsNew" = $2, "jobsAdded" = $3, errors = $4, "finishedAt" = $5
        WHERE id = $6""",
        state["posts_found"],
        state["posts_new"],
        jobs_added,
        state["errors"],
        now,
        state["scan_run_id"],
    )

    return {"jobs_added": jobs_added}


def _build_listing_payload(source_name: str, post: dict, item: dict) -> dict:
    metadata = dict(post.get("metadata") or {})

    if source_name == "hackernews":
        header_line = _coerce_string(metadata.get("headerLine")) or _derive_title(
            post["raw_content"]
        )
        if post.get("author") and not metadata.get("hnAuthor"):
            metadata["hnAuthor"] = post["author"]
        metadata["headerLine"] = header_line

        return {
            "title": _truncate_title(header_line),
            "company": post.get("author") or "Unknown",
            "description": post["raw_content"],
            "location": None,
            "salary": None,
            "url": post.get("permalink"),
            "jobType": None,
            "applyUrl": None,
            "embeddingText": item.get("embedding_text"),
            "metadata": metadata,
        }

    return {
        "title": _derive_title(post["raw_content"]),
        "company": post.get("author") or "Unknown",
        "description": post["raw_content"],
        "location": None,
        "salary": None,
        "url": post.get("permalink"),
        "jobType": None,
        "applyUrl": None,
        "embeddingText": item.get("embedding_text"),
        "metadata": metadata,
    }


def _coerce_string(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _derive_title(raw_content: str) -> str:
    first_line = raw_content.split("\n", 1)[0].strip()
    if first_line.startswith("Title:"):
        first_line = first_line[len("Title:") :].strip()
    return _truncate_title(first_line or "Untitled")


def _truncate_title(value: str) -> str:
    if len(value) > 150:
        return value[:147] + "..."
    return value
