from datetime import datetime, UTC

import httpx

from pipeline.sources.hackernews.constants import FIREBASE_BASE
from pipeline.sources.hackernews.parser import hn_html_to_plain
from pipeline.state import RawPostData


async def fetch_jobstories(
    client: httpx.AsyncClient,
    since: datetime | None,
) -> list[RawPostData]:
    resp = await client.get(f"{FIREBASE_BASE}/jobstories.json")
    if resp.status_code != 200:
        return []

    job_ids: list[int] = resp.json()
    if not job_ids:
        return []

    posts: list[RawPostData] = []

    for job_id in job_ids:
        item_resp = await client.get(f"{FIREBASE_BASE}/item/{job_id}.json")
        if item_resp.status_code != 200:
            continue

        item = item_resp.json()
        if not item or item.get("type") != "job" or item.get("deleted"):
            continue

        created_at = None
        if item.get("time"):
            created_at = datetime.fromtimestamp(item["time"], tz=UTC)

        if since and created_at and created_at < since:
            continue

        title = item.get("title", "")
        text_html = item.get("text", "")
        plain_text = hn_html_to_plain(text_html) if text_html else ""
        content = f"Title: {title}"
        if plain_text:
            content += f"\n\nBody: {plain_text}"

        posted_at = created_at.isoformat() if created_at else None
        author = item.get("by", "")

        posts.append(
            {
                "external_id": f"hn_job_{job_id}",
                "raw_content": content,
                "permalink": f"https://news.ycombinator.com/item?id={job_id}",
                "author": author or None,
                "posted_at": posted_at,
                "metadata": {
                    "points": item.get("score", 0),
                    "title": title,
                },
            }
        )

    return posts
