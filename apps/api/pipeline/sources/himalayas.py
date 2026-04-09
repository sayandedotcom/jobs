from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.sources.utils import html_to_plain
from pipeline.state import RawPostData


@register_source
class HimalayasService(BaseSource):
    """Himalayas remote job board source using the public JSON API.

    Service details:
        - Browse: https://himalayas.app/jobs/api?limit=20&offset={n}
        - Search: https://himalayas.app/jobs/api/search?q={query}&page={n}
        - No API key required
        - Max 20 jobs per request, offset/page-based pagination
        - Each job includes HTML description, company info, salary, location

    Fetch strategies (selected via sub_source 'type' in DB):
        - "search": sub_source.name = search query (e.g., "react engineer")
                    Fetches matching jobs from Himalayas search endpoint.
        - "browse": sub_source.name = ignored
                    Fetches latest jobs from the browse endpoint.
    """

    BROWSE_URL = "https://himalayas.app/jobs/api"
    SEARCH_URL = "https://himalayas.app/jobs/api/search"
    PAGE_LIMIT = 20
    MAX_PAGES = 10

    def get_source_name(self) -> str:
        return "himalayas"

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

                if sub_type == "search":
                    fetched = await self._fetch_search(client, name, since)
                else:
                    fetched = await self._fetch_browse(client, since)

                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    def _parse_job(self, job: dict) -> RawPostData | None:
        guid = job.get("guid", "")
        if not guid:
            return None

        external_id = f"himalayas_{guid}"

        title = job.get("title", "")
        company_name = job.get("companyName", "")
        description_html = job.get("description", "")
        description = html_to_plain(description_html) if description_html else ""

        locations = job.get("locationRestrictions") or []
        location_str = ", ".join(locations) if isinstance(locations, list) else ""

        categories = job.get("categories") or []
        category_str = ", ".join(categories) if isinstance(categories, list) else ""

        employment_type = job.get("employmentType", "")
        seniority_list = job.get("seniority") or []
        seniority_str = (
            ", ".join(seniority_list) if isinstance(seniority_list, list) else ""
        )

        min_salary = job.get("minSalary")
        max_salary = job.get("maxSalary")
        currency = job.get("currency", "")

        raw_parts = [f"Title: {title}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if location_str:
            raw_parts.append(f"Location: {location_str}")
        if category_str:
            raw_parts.append(f"Categories: {category_str}")
        if employment_type:
            raw_parts.append(f"Employment: {employment_type}")
        if seniority_str:
            raw_parts.append(f"Seniority: {seniority_str}")
        if min_salary or max_salary:
            salary_parts = []
            if min_salary:
                salary_parts.append(str(min_salary))
            if max_salary:
                salary_parts.append(str(max_salary))
            salary_range = "-".join(salary_parts)
            if currency:
                salary_range = f"{salary_range} {currency}"
            raw_parts.append(f"Salary: {salary_range}")
        if description:
            raw_parts.append(f"\n{description}")

        pub_ts = job.get("pubDate")
        posted_at = None
        if pub_ts is not None:
            with suppress(ValueError, TypeError, OSError):
                posted_at = datetime.fromtimestamp(pub_ts, tz=datetime.UTC).isoformat()

        permalink = job.get("applicationLink") or guid

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": company_name or None,
            "posted_at": posted_at,
            "metadata": {},
        }

    async def _fetch_browse(
        self,
        client: httpx.AsyncClient,
        since: datetime | None,
    ) -> list[RawPostData]:
        posts: list[RawPostData] = []
        offset = 0
        pages_fetched = 0

        while pages_fetched < self.MAX_PAGES:
            resp = await client.get(
                self.BROWSE_URL,
                params={"limit": self.PAGE_LIMIT, "offset": offset},
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            jobs = data.get("jobs", [])
            if not jobs:
                break

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

            if len(jobs) < self.PAGE_LIMIT:
                break

            offset += self.PAGE_LIMIT
            pages_fetched += 1

        return posts

    async def _fetch_search(
        self,
        client: httpx.AsyncClient,
        query: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        posts: list[RawPostData] = []
        page = 1

        for _ in range(self.MAX_PAGES):
            resp = await client.get(
                self.SEARCH_URL,
                params={"q": query, "page": page},
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            jobs = data.get("jobs", [])
            if not jobs:
                break

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

            if len(jobs) < self.PAGE_LIMIT:
                break

            page += 1

        return posts
