from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.sources.utils import html_to_plain
from pipeline.state import RawPostData


@register_source
class ArbeitnowService(BaseSource):
    """Arbeitnow job board source using the public JSON API.

    Service details:
        - https://www.arbeitnow.com/api/job-board-api
        - No API key required
        - Paginated via links.next (cursor-based), 100 jobs per page
        - Each job includes HTML description, company, tags, job types, location
        - created_at is a Unix timestamp

    Fetch strategies (selected via sub_source 'type' in DB):
        - "browse": sub_source.name = ignored (fetches all jobs)
        - "search": sub_source.name = search query (adds ?search={query} param)
    """

    API_URL = "https://www.arbeitnow.com/api/job-board-api"
    MAX_PAGES = 10

    def get_source_name(self) -> str:
        return "arbeitnow"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                name = sub["name"]
                sub_type = sub.get("type", "browse")

                search_query = name if sub_type == "search" else ""
                fetched = await self._fetch(client, search_query, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch(
        self,
        client: httpx.AsyncClient,
        search_query: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        posts: list[RawPostData] = []
        next_url: str | None = self.API_URL
        pages_fetched = 0

        if search_query:
            next_url = f"{self.API_URL}?search={search_query}"

        while next_url and pages_fetched < self.MAX_PAGES:
            resp = await client.get(next_url)
            if resp.status_code != 200:
                break

            data = resp.json()
            jobs = data.get("data", [])

            for job in jobs:
                post = self._parse_job(job)
                if post is None:
                    continue

                if since and post.get("posted_at"):
                    with suppress(ValueError, TypeError):
                        posted = datetime.fromisoformat(post["posted_at"])
                        if posted < since:
                            continue

                posts.append(post)

            links = data.get("links", {})
            next_url = links.get("next") or None
            pages_fetched += 1

        return posts

    def _parse_job(self, job: dict) -> RawPostData | None:
        slug = job.get("slug", "")
        if not slug:
            return None

        external_id = f"an_{slug}"

        title = job.get("title", "")
        company_name = job.get("company_name", "")
        description_html = job.get("description", "")
        description = html_to_plain(description_html) if description_html else ""

        remote = job.get("remote", False)
        location = job.get("location", "")
        tags = job.get("tags") or []
        tags_str = ", ".join(tags) if isinstance(tags, list) else ""
        job_types = job.get("job_types") or []
        job_types_str = ", ".join(job_types) if isinstance(job_types, list) else ""

        raw_parts = [f"Title: {title}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if location:
            raw_parts.append(f"Location: {location}")
        if remote:
            raw_parts.append("Remote: Yes")
        if tags_str:
            raw_parts.append(f"Tags: {tags_str}")
        if job_types_str:
            raw_parts.append(f"Job Types: {job_types_str}")
        if description:
            raw_parts.append(f"\n{description}")

        posted_at = None
        created_ts = job.get("created_at")
        if created_ts is not None:
            with suppress(ValueError, TypeError, OSError):
                posted_at = datetime.fromtimestamp(
                    created_ts, tz=datetime.timezone.utc
                ).isoformat()

        permalink = job.get("url") or None

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": company_name or None,
            "posted_at": posted_at,
            "metadata": {},
        }
