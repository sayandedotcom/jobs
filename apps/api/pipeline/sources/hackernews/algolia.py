from contextlib import suppress
from datetime import datetime

import httpx

from pipeline.sources.hackernews.constants import ALGOLIA_BASE
from pipeline.sources.hackernews.parser import (
    extract_header_line,
    hn_html_to_plain,
    normalize_plain_text,
)
from pipeline.state import RawPostData


async def fetch_whoishiring(
    client: httpx.AsyncClient,
    name: str,
    since: datetime | None,
    hits_per_page: int,
) -> list[RawPostData]:
    story = await _resolve_story(client, name)
    if not story:
        return []
    story_id, story_title = story

    posts: list[RawPostData] = []
    page = 0
    nb_pages = 1

    while page < nb_pages:
        resp = await client.get(
            f"{ALGOLIA_BASE}/search",
            params={
                "tags": f"comment,story_{story_id}",
                "page": page,
                "hitsPerPage": hits_per_page,
            },
        )
        if resp.status_code != 200:
            break

        data = resp.json()
        nb_pages = data.get("nbPages", 1)

        for hit in data.get("hits", []):
            parent_id = hit.get("parent_id")
            if parent_id is not None:
                with suppress(TypeError, ValueError):
                    if int(parent_id) != story_id:
                        continue

            created_at_str = hit.get("created_at", "")
            created_at = None
            if created_at_str:
                with suppress(ValueError, TypeError):
                    created_at = datetime.fromisoformat(created_at_str)
                    if created_at.tzinfo is not None:
                        created_at = created_at.replace(tzinfo=None)

            if since and created_at and created_at < since:
                continue

            comment_html = hit.get("comment_text") or hit.get("text") or ""
            plain_text = normalize_plain_text(hn_html_to_plain(comment_html))
            if not plain_text.strip():
                continue

            object_id = hit.get("objectID", "")
            if not object_id:
                continue
            author = hit.get("author", "")
            posted_at = created_at.isoformat() if created_at else None
            header_line = extract_header_line(plain_text)

            posts.append(
                {
                    "external_id": f"hn_{object_id}",
                    "raw_content": plain_text,
                    "permalink": f"https://news.ycombinator.com/item?id={object_id}",
                    "author": author or None,
                    "posted_at": posted_at,
                    "metadata": {
                        "commentId": object_id,
                        "headerLine": header_line,
                        "htmlContent": comment_html,
                        "hnAuthor": author or None,
                        "storyId": story_id,
                        "storyTitle": story_title,
                        "type": "whoishiring",
                    },
                }
            )

        page += 1

    return posts


async def _resolve_story(
    client: httpx.AsyncClient, name: str
) -> tuple[int, str | None] | None:
    if name and name.lower() != "latest":
        try:
            story_id = int(name)
            return story_id, await _fetch_story_title(client, story_id)
        except ValueError:
            pass

    resp = await client.get(
        f"{ALGOLIA_BASE}/search_by_date",
        params={
            "tags": "story,author_whoishiring",
            "query": "Ask HN: Who is hiring?",
            "hitsPerPage": 5,
            "page": 0,
        },
    )
    if resp.status_code != 200:
        return None

    data = resp.json()
    for hit in data.get("hits", []):
        title = hit.get("title") or ""
        if "who is hiring" in title.lower():
            return int(hit["objectID"]), title

    return None


async def _fetch_story_title(client: httpx.AsyncClient, story_id: int) -> str | None:
    from pipeline.sources.hackernews.constants import FIREBASE_BASE

    resp = await client.get(f"{FIREBASE_BASE}/item/{story_id}.json")
    if resp.status_code == 200:
        item = resp.json() or {}
        title = item.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()

    return None
