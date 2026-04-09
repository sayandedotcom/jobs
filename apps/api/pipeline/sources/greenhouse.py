from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.sources.utils import html_to_plain
from pipeline.state import RawPostData


@register_source
class GreenhouseService(BaseSource):
    """Greenhouse job board source using the public Harvest Job Board API.

    Service details:
        - Uses the public Greenhouse Job Board API:
            https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true
        - No API key required for public boards
        - Each company on Greenhouse has a unique board token (e.g., "stripe", "notion")

    Fetch strategies (selected via sub_source 'type' in DB):
        - "board": sub_source.name = company board token (e.g., "stripe", "notion")
                   Fetches all active jobs from that company's Greenhouse board.

    Scalability notes:
        - The API returns up to 200 jobs per page (paginated via ?page=N)
        - Each company board is fetched independently
        - httpx.AsyncClient is created per fetch call and properly closed
    """

    API_BASE = "https://boards-api.greenhouse.io/v1/boards"

    def get_source_name(self) -> str:
        return "greenhouse"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        """Fetch jobs from Greenhouse boards specified in sub_sources.

        Args:
            sub_sources: List of dicts with 'name' and 'type' keys, e.g.:
                         [{'name': 'stripe', 'type': 'board'},
                          {'name': 'notion', 'type': 'board'}]
            since:       Only return jobs updated after this timestamp.

        Returns:
            Deduplicated list of RawPostData (deduped by external_id).
        """
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                company = sub["name"]
                fetched = await self._fetch_board(client, company, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_board(
        self,
        client: httpx.AsyncClient,
        company: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        """Fetch all active jobs from a company's Greenhouse board.

        Paginates through all pages of results for the given company.
        Each job's content (description) is included via ?content=true.
        """
        posts: list[RawPostData] = []
        page = 0

        while True:
            resp = await client.get(
                f"{self.API_BASE}/{company}/jobs",
                params={"content": "true", "page": page},
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            jobs = data.get("jobs", [])
            if not jobs:
                break

            for job in jobs:
                external_id = f"gh_{company}_{job['id']}"

                updated_at = None
                updated_at_str = job.get("updated_at", "")
                if updated_at_str:
                    with suppress(ValueError, TypeError):
                        updated_at = datetime.fromisoformat(updated_at_str)

                if since and updated_at and updated_at < since:
                    continue

                title = job.get("title", "")
                location = job.get("location", {})
                location_name = (
                    location.get("name", "") if isinstance(location, dict) else ""
                )
                content_html = job.get("content", "")
                description = html_to_plain(content_html) if content_html else ""

                raw_parts = [f"Title: {title}"]
                if location_name:
                    raw_parts.append(f"Location: {location_name}")
                raw_parts.append(f"Company: {company}")
                if description:
                    raw_parts.append(f"\n{description}")

                posted_at = updated_at.isoformat() if updated_at else None
                permalink = job.get("absolute_url") or None

                posts.append(
                    {
                        "external_id": external_id,
                        "raw_content": "\n".join(raw_parts),
                        "permalink": permalink,
                        "author": company,
                        "posted_at": posted_at,
                        "metadata": {},
                    }
                )

            page += 1

        return posts
