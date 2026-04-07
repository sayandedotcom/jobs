import re
from contextlib import suppress
from datetime import datetime, UTC
from html.parser import HTMLParser

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


class _HTMLStripper(HTMLParser):
    """Minimal HTML-to-plain-text converter for HN comment bodies."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self._parts.append(value)
                    self._parts.append(" ")
        elif tag in ("p", "br", "li"):
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts).strip()


def _html_to_plain(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


def _extract_company_from_comment(text: str) -> str:
    """Extract company name from HN 'Who is hiring?' comment header.

    HN hiring comments follow a convention:
        Company Name | Role | Location | ...
    The first line typically contains pipe-delimited fields.
    """
    first_line = text.split("\n", 1)[0].strip()
    # Remove leading bullet/dash characters
    first_line = re.sub(r"^[\s\-•*|]+", "", first_line).strip()
    # Split on pipe or em-dash (common delimiters in HN comments)
    parts = re.split(r"\s*[|–—]\s*", first_line, maxsplit=1)
    return parts[0].strip() if parts else "Unknown"


@register_source
class HackerNewsService(BaseSource):
    """Unified Hacker News service with multiple fetch strategies.

    Service details:
        - Uses two APIs, neither requires authentication:
            1. Algolia HN Search API (https://hn.algolia.com/api/v1)
               — used for "whoishiring" strategy
            2. Official HN Firebase API (https://hacker-news.firebaseio.com/v0)
               — used for "jobstories" strategy
        - No API keys or credentials needed
        - Algolia rate limits: ~10000 requests/hour (generous)
        - Firebase API: no documented rate limit

    Fetch strategies (selected via sub_source 'type' in DB):
        - "whoishiring": Fetches comments from "Ask HN: Who is hiring?" threads.
                         sub_source.name = "latest" (auto-finds newest thread) or
                                           a story ID (e.g., "43864723")
        - "jobstories":  Fetches items with type="job" from the HN Firebase API.
                         sub_source.name = ignored (fetches all recent job stories)

    Scalability notes:
        - "whoishiring" paginates through all comments (200/page via Algolia)
        - "jobstories" fetches up to 200 job IDs + individual item lookups
        - All HTTP calls are sequential; consider asyncio.gather() for item lookups
        - httpx.AsyncClient is created per fetch call and properly closed
    """

    ALGOLIA_BASE = "https://hn.algolia.com/api/v1"
    FIREBASE_BASE = "https://hacker-news.firebaseio.com/v0"
    HITS_PER_PAGE = 200

    def get_source_name(self) -> str:
        return "hackernews"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        """Dispatch to the appropriate fetch strategy based on sub_source type.

        Args:
            sub_sources: List of dicts with 'name' and 'type' keys, e.g.:
                         [{'name': 'latest', 'type': 'whoishiring'},
                          {'name': 'default', 'type': 'jobstories'}]
            since:       Only return posts newer than this timestamp (incremental fetch).

        Returns:
            Deduplicated list of RawPostData (deduped by external_id).
        """
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                name = sub["name"]
                sub_type = sub.get("type", "whoishiring")

                if sub_type == "jobstories":
                    fetched = await self._fetch_jobstories(client, since)
                else:
                    fetched = await self._fetch_whoishiring(client, name, since)

                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_whoishiring(
        self,
        client: httpx.AsyncClient,
        name: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        """Fetch comments from "Ask HN: Who is hiring?" monthly threads via Algolia.

        Two-step process:
            1. Find the target story (latest thread or specific story ID)
            2. Paginate through all comments on that story

        HN "Who is hiring?" threads are posted monthly by user "whoishiring".
        Each thread typically contains 200-800 job postings as top-level comments.
        Comments follow a convention: "Company | Role | Location | ..."
        """
        story_id = await self._resolve_story_id(client, name)
        if not story_id:
            return []

        posts: list[RawPostData] = []
        page = 0
        nb_pages = 1

        while page < nb_pages:
            resp = await client.get(
                f"{self.ALGOLIA_BASE}/search",
                params={
                    "tags": f"comment,story_{story_id}",
                    "page": page,
                    "hitsPerPage": self.HITS_PER_PAGE,
                },
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            nb_pages = data.get("nbPages", 1)

            for hit in data.get("hits", []):
                created_at_str = hit.get("created_at", "")
                created_at = None
                if created_at_str:
                    with suppress(ValueError, TypeError):
                        created_at = datetime.fromisoformat(created_at_str)

                if since and created_at and created_at < since:
                    continue

                comment_html = hit.get("comment_text") or hit.get("text") or ""
                plain_text = _html_to_plain(comment_html)
                if not plain_text.strip():
                    continue

                object_id = hit.get("objectID", "")
                author = hit.get("author", "")
                posted_at = created_at.isoformat() if created_at else None

                posts.append(
                    {
                        "external_id": f"hn_{object_id}",
                        "raw_content": plain_text,
                        "permalink": f"https://news.ycombinator.com/item?id={object_id}",
                        "author": author or None,
                        "posted_at": posted_at,
                        "metadata": {
                            "points": hit.get("points", 0),
                            "story_id": story_id,
                            "parent_story_title": None,
                        },
                    }
                )

            page += 1

        return posts

    async def _resolve_story_id(
        self, client: httpx.AsyncClient, name: str
    ) -> int | None:
        """Resolve a sub_source name to an HN story ID.

        If name is "latest" or empty, searches Algolia for the newest
        "Ask HN: Who is hiring?" thread. Otherwise treats name as a numeric story ID.
        """
        if name and name.lower() != "latest":
            try:
                return int(name)
            except ValueError:
                pass

        resp = await client.get(
            f"{self.ALGOLIA_BASE}/search_by_date",
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
            title = (hit.get("title") or "").lower()
            if "who is hiring" in title:
                return int(hit["objectID"])

        return None

    async def _fetch_jobstories(
        self,
        client: httpx.AsyncClient,
        since: datetime | None,
    ) -> list[RawPostData]:
        """Fetch items with type='job' from the official HN Firebase API.

        Uses the /v0/jobstories endpoint which returns up to 200 job story IDs.
        Each ID is then fetched individually via /v0/item/<id>.json.
        Job items on HN are company-posted listings (distinct from "Who is hiring?" comments).
        """
        resp = await client.get(f"{self.FIREBASE_BASE}/jobstories.json")
        if resp.status_code != 200:
            return []

        job_ids: list[int] = resp.json()
        if not job_ids:
            return []

        posts: list[RawPostData] = []

        # HN jobstories returns newest first; fetch items sequentially
        for job_id in job_ids:
            item_resp = await client.get(f"{self.FIREBASE_BASE}/item/{job_id}.json")
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
            plain_text = _html_to_plain(text_html) if text_html else ""
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
