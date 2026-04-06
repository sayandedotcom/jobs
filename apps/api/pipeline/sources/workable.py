import re
from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


def _html_to_plain(html: str) -> str:
    """Strip HTML tags to get plain text from Workable job descriptions."""
    text = html
    for tag in ("</p>", "</li>", "</div>", "<br>", "<br/>", "<br />"):
        text = text.replace(tag, "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&#39;", "'")
    text = text.replace("&quot;", '"')
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


@register_source
class WorkableService(BaseSource):
    """Workable job board source using the public jobs API.

    Service details:
        - Uses the Workable public jobs API:
            https://jobs.workable.com/api/v1/jobs?query={search}&limit={n}
        - No API key required
        - Returns jobs across all companies on Workable; filter by query
        - Each job includes full HTML description, company info, and location

    Fetch strategies (selected via sub_source 'type' in DB):
        - "search": sub_source.name = search query (e.g., "software engineer remote")
                    Fetches matching jobs from Workable's global job board.
        - "board":  sub_source.name = ignored (fetches latest jobs from all companies)

    Scalability notes:
        - The API paginates via nextPageToken (up to 20 jobs per page)
        - Each page is fetched sequentially
        - httpx.AsyncClient is created per fetch call and properly closed
    """

    API_BASE = "https://jobs.workable.com/api/v1/jobs"
    PAGE_LIMIT = 20
    MAX_PAGES = 10

    def get_source_name(self) -> str:
        return "workable"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        """Fetch jobs from Workable for the given sub_sources.

        Args:
            sub_sources: List of dicts with 'name' and 'type' keys, e.g.:
                         [{'name': 'software engineer', 'type': 'search'},
                          {'name': 'default', 'type': 'board'}]
            since:       Only return jobs created after this timestamp.

        Returns:
            Deduplicated list of RawPostData (deduped by external_id).
        """
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                name = sub["name"]
                sub_type = sub.get("type", "search")

                query = "" if sub_type == "board" else name

                fetched = await self._fetch_jobs(client, query, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_jobs(
        self,
        client: httpx.AsyncClient,
        query: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        """Fetch jobs from Workable API with pagination.

        Paginates through pages using nextPageToken up to MAX_PAGES.
        Filters by 'since' timestamp on the 'created' field.
        """
        posts: list[RawPostData] = []
        page_token: str | None = None
        pages_fetched = 0

        while pages_fetched < self.MAX_PAGES:
            params: dict = {"limit": self.PAGE_LIMIT}
            if query:
                params["query"] = query
            if page_token:
                params["pageToken"] = page_token

            resp = await client.get(self.API_BASE, params=params)
            if resp.status_code != 200:
                break

            data = resp.json()
            jobs = data.get("jobs", [])

            if not jobs:
                break

            for job in jobs:
                job_id = job.get("id", "")
                if not job_id:
                    continue

                company = job.get("company", {})
                company_name = ""
                if isinstance(company, dict):
                    company_name = company.get("title", "")

                external_id = f"workable_{job_id}"

                created_at = None
                created_str = job.get("created", "")
                if created_str:
                    with suppress(ValueError, TypeError):
                        created_at = datetime.fromisoformat(
                            created_str.replace("Z", "+00:00")
                        )

                if since and created_at and created_at < since:
                    continue

                title = job.get("title", "")
                description_html = job.get("description", "")
                description = (
                    _html_to_plain(description_html) if description_html else ""
                )
                requirements_html = job.get("requirementsSection", "")
                requirements = (
                    _html_to_plain(requirements_html) if requirements_html else ""
                )
                benefits_html = job.get("benefitsSection", "")
                benefits = _html_to_plain(benefits_html) if benefits_html else ""

                location = job.get("location", {})
                location_str = ""
                if isinstance(location, dict):
                    parts = [
                        location.get("city", ""),
                        location.get("subregion", ""),
                        location.get("countryName", ""),
                    ]
                    location_str = ", ".join(p for p in parts if p)

                employment_type = job.get("employmentType", "")
                workplace = job.get("workplace", "")
                department = job.get("department", "")

                raw_parts = [f"Title: {title}"]
                if company_name:
                    raw_parts.append(f"Company: {company_name}")
                if location_str:
                    raw_parts.append(f"Location: {location_str}")
                if department:
                    raw_parts.append(f"Department: {department}")
                if employment_type:
                    raw_parts.append(f"Employment: {employment_type}")
                if workplace:
                    raw_parts.append(f"Workplace: {workplace}")
                if description:
                    raw_parts.append(f"\n{description}")
                if requirements:
                    raw_parts.append(f"\nRequirements:\n{requirements}")
                if benefits:
                    raw_parts.append(f"\nBenefits:\n{benefits}")

                posted_at = created_at.isoformat() if created_at else None
                permalink = job.get("url") or None

                posts.append(
                    {
                        "external_id": external_id,
                        "raw_content": "\n".join(raw_parts),
                        "permalink": permalink,
                        "author": company_name or None,
                        "posted_at": posted_at,
                    }
                )

            page_token = data.get("nextPageToken")
            if not page_token:
                break
            pages_fetched += 1

        return posts
