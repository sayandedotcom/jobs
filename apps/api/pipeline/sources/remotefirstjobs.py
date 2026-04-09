from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.sources.utils import html_to_plain
from pipeline.state import RawPostData


@register_source
class RemotefirstjobsService(BaseSource):
    """RemoteFirstJobs (JobsCollider) source using the public JSON API.

    Service details:
        - https://remotefirstjobs.com/api/search-jobs?category={cat}&page={n}
        - No API key required
        - Max 100 jobs/page, up to 5 pages (500 jobs per category)
        - 16 categories, updated every 10 min
        - Each job includes HTML description, company, salary, seniority, locations

    Fetch strategies (selected via sub_source 'type' in DB):
        - "category": sub_source.name = category slug (e.g., "software_development")
        - "browse":   sub_source.name = ignored (fetches software_development)

    Categories: software_development, cybersecurity, customer_service, design,
    marketing, sales, product, business, data, devops, finance_legal,
    human_resources, qa, writing, project_management, all_others
    """

    API_URL = "https://remotefirstjobs.com/api/search-jobs"
    PAGE_SIZE = 100
    MAX_PAGES = 5

    def get_source_name(self) -> str:
        return "remotefirstjobs"

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
                sub_type = sub.get("type", "category")

                category = name if sub_type == "category" else "software_development"
                fetched = await self._fetch_category(client, category, since)

                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_category(
        self,
        client: httpx.AsyncClient,
        category: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        posts: list[RawPostData] = []

        for page in range(self.MAX_PAGES):
            resp = await client.get(
                self.API_URL,
                params={"category": category, "page": page},
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            jobs = data.get("jobs", [])
            jobs_count = data.get("jobs_count", 0)

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

            if jobs_count < self.PAGE_SIZE:
                break

        return posts

    def _parse_job(self, job: dict) -> RawPostData | None:
        job_id = job.get("id", "")
        if not job_id:
            return None

        external_id = f"rfj_{job_id}"

        title = job.get("title", "")
        company_name = job.get("company_name", "")
        description_html = job.get("description", "")
        description = html_to_plain(description_html) if description_html else ""

        locations = job.get("locations") or []
        location_str = ", ".join(locations) if isinstance(locations, list) else ""

        category = job.get("category", "")
        seniority = job.get("seniority", "")

        salary_min = job.get("salary_min", 0)
        salary_max = job.get("salary_max", 0)

        raw_parts = [f"Title: {title}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if location_str:
            raw_parts.append(f"Location: {location_str}")
        if category:
            raw_parts.append(f"Category: {category}")
        if seniority:
            raw_parts.append(f"Seniority: {seniority}")
        if salary_min or salary_max:
            salary_parts = []
            if salary_min:
                salary_parts.append(str(salary_min))
            if salary_max:
                salary_parts.append(str(salary_max))
            raw_parts.append(f"Salary: {'-'.join(salary_parts)}")
        if description:
            raw_parts.append(f"\n{description}")

        posted_at = None
        published_str = job.get("published_at", "")
        if published_str:
            with suppress(ValueError, TypeError):
                posted_at = datetime.fromisoformat(published_str).isoformat()

        permalink = job.get("url") or None

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": company_name or None,
            "posted_at": posted_at,
            "metadata": {},
        }
