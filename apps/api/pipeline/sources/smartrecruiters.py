import re
from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


def _html_to_plain(html: str) -> str:
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
class SmartrecruitersService(BaseSource):
    """SmartRecruiters job board source using the public postings API.

    Service details:
        - Uses the SmartRecruiters public job postings API:
            https://api.smartrecruiters.com/v1/companies/{company_id}/postings
        - No API key required for public postings
        - Each company has a unique identifier (e.g., "smartrecruiters", "nvidia")
        - The list endpoint returns metadata only (no full description)
        - Full descriptions would require fetching each job individually

    Fetch strategies (selected via sub_source 'type' in DB):
        - "company": sub_source.name = company identifier (e.g., "smartrecruiters")
                     Fetches all active postings from that company's board.

    Scalability notes:
        - Offset-based pagination, up to 100 jobs per page
        - Each company board is fetched independently
        - httpx.AsyncClient is created per fetch call and properly closed
    """

    API_BASE = "https://api.smartrecruiters.com/v1/companies"
    PAGE_SIZE = 100

    def get_source_name(self) -> str:
        return "smartrecruiters"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                company_id = sub["name"]
                fetched = await self._fetch_company(client, company_id, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_company(
        self,
        client: httpx.AsyncClient,
        company_id: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        posts: list[RawPostData] = []
        offset = 0

        while True:
            resp = await client.get(
                f"{self.API_BASE}/{company_id}/postings",
                params={"limit": self.PAGE_SIZE, "offset": offset},
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            jobs = data.get("content", [])
            if not jobs:
                break

            for job in jobs:
                post = self._parse_job(job, company_id)
                if post is None:
                    continue

                if since and post.get("posted_at"):
                    with suppress(ValueError, TypeError):
                        posted = datetime.fromisoformat(post["posted_at"])
                        if posted < since:
                            continue

                posts.append(post)

            total_found = data.get("totalFound", 0)
            offset += self.PAGE_SIZE
            if offset >= total_found:
                break

        return posts

    def _parse_job(self, job: dict, company_id: str) -> RawPostData | None:
        job_id = job.get("id", "")
        if not job_id:
            return None

        external_id = f"sr_{job_id}"

        title = job.get("name", "")

        company_info = job.get("company", {})
        company_name = (
            company_info.get("name", "") if isinstance(company_info, dict) else ""
        )

        location = job.get("location", {})
        location_parts: list[str] = []
        if isinstance(location, dict):
            for field in ("city", "region", "country"):
                val = location.get(field, "")
                if val:
                    location_parts.append(val)
        location_str = ", ".join(location_parts)

        remote = location.get("remote", False) if isinstance(location, dict) else False

        department = job.get("department", {})
        department_label = (
            department.get("label", "") if isinstance(department, dict) else ""
        )

        function = job.get("function", {})
        function_label = function.get("label", "") if isinstance(function, dict) else ""

        employment_type = job.get("typeOfEmployment", {})
        employment_label = (
            employment_type.get("label", "")
            if isinstance(employment_type, dict)
            else ""
        )

        raw_parts = [f"Title: {title}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if location_str:
            raw_parts.append(f"Location: {location_str}")
        if remote:
            raw_parts.append("Remote: Yes")
        if department_label:
            raw_parts.append(f"Department: {department_label}")
        if function_label:
            raw_parts.append(f"Function: {function_label}")
        if employment_label:
            raw_parts.append(f"Employment: {employment_label}")

        posted_at = None
        released_str = job.get("releasedDate", "")
        if released_str:
            with suppress(ValueError, TypeError):
                posted_at = datetime.fromisoformat(
                    released_str.replace("Z", "+00:00")
                ).isoformat()

        permalink = job.get("ref") or None

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": company_name or company_id,
            "posted_at": posted_at,
            "metadata": {},
        }
