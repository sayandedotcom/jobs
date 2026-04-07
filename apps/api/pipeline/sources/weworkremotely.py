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


CATEGORY_MAP: dict[int, str] = {
    1: "Design",
    2: "Full-Stack Programming",
    17: "Front-End Programming",
    18: "Back-End Programming",
    7: "Customer Support",
    6: "DevOps and Sysadmin",
    9: "Sales and Marketing",
    3: "Management and Finance",
    11: "Product",
    4: "All Other Remote",
}


@register_source
class WeworkremotelyService(BaseSource):
    """WeWorkRemotely remote job board source using the authenticated JSON API.

    Service details:
        - GET https://weworkremotely.com/api/v1/remote-jobs
        - Bearer token auth (1,000 requests/day)
        - Supports ETag / If-None-Match for conditional requests
        - Returns all active jobs with structured fields
        - Email api@weworkremotely.com to request a token

    Fetch strategies (selected via sub_source 'type' in DB):
        - "browse": sub_source.name = ignored (fetches all jobs)
    """

    API_URL = "https://weworkremotely.com/api/v1/remote-jobs"

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    def get_source_name(self) -> str:
        return "weworkremotely"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for _sub in sub_sources:
                fetched = await self._fetch_all(client, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_all(
        self,
        client: httpx.AsyncClient,
        since: datetime | None,
    ) -> list[RawPostData]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        resp = await client.get(self.API_URL, headers=headers)
        if resp.status_code != 200:
            return []

        data = resp.json()
        if not isinstance(data, list):
            return []

        posts: list[RawPostData] = []
        for job in data:
            if not isinstance(job, dict):
                continue

            post = self._parse_job(job)
            if post is None:
                continue

            if since and post.get("posted_at"):
                with suppress(ValueError, TypeError):
                    posted = datetime.fromisoformat(post["posted_at"])
                    if posted < since:
                        continue

            posts.append(post)

        return posts

    def _parse_job(self, job: dict) -> RawPostData | None:
        job_id = job.get("id")
        if not job_id:
            return None

        external_id = f"wwr_{job_id}"

        title = job.get("title", "")
        company_name = job.get("company", "")
        description_html = job.get("description", "")
        description = _html_to_plain(description_html) if description_html else ""

        location = job.get("location", "")
        region = job.get("region", "")
        category_id = job.get("category_id")
        category = CATEGORY_MAP.get(category_id, "") if category_id else ""
        job_type = job.get("job_listing_type", "")
        salary = job.get("salary_range", "")
        url = job.get("url", "")

        raw_parts = [f"Title: {title}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if location:
            raw_parts.append(f"Location: {location}")
        if region:
            raw_parts.append(f"Region: {region}")
        if category:
            raw_parts.append(f"Category: {category}")
        if job_type:
            raw_parts.append(f"Type: {job_type}")
        if salary and salary != "Prefer not to share":
            raw_parts.append(f"Salary: {salary}")
        if url:
            raw_parts.append(f"Company URL: {url}")
        if description:
            raw_parts.append(f"\n{description}")

        posted_at = None
        created_str = job.get("created_at", "")
        if created_str:
            with suppress(ValueError, TypeError):
                posted_at = datetime.fromisoformat(
                    created_str.replace("Z", "+00:00")
                ).isoformat()

        permalink = (
            f"https://weworkremotely.com/remote-jobs/{job_id}" if job_id else None
        )

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": company_name or None,
            "posted_at": posted_at,
        }
