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
class RemoteokService(BaseSource):
    """RemoteOK remote job board source using the public JSON API.

    Service details:
        - https://remoteok.com/api
        - No API key required
        - Single GET returns all current jobs (no pagination)
        - Response is a JSON array: first element is metadata, rest are jobs
        - Each job includes HTML description, company, tags, location, salary

    Fetch strategies (selected via sub_source 'type' in DB):
        - "browse": sub_source.name = ignored (fetches all jobs)
    """

    API_URL = "https://remoteok.com/api"

    def get_source_name(self) -> str:
        return "remoteok"

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
        resp = await client.get(self.API_URL)
        if resp.status_code != 200:
            return []

        data = resp.json()
        if not isinstance(data, list):
            return []

        posts: list[RawPostData] = []
        for item in data:
            if not isinstance(item, dict) or "id" not in item:
                continue

            post = self._parse_job(item)
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
        job_id = job.get("id", "")
        if not job_id:
            return None

        external_id = f"rok_{job_id}"

        position = job.get("position", "")
        company_name = job.get("company", "")
        description_html = job.get("description", "")
        description = _html_to_plain(description_html) if description_html else ""

        location = job.get("location", "")
        tags = job.get("tags") or []
        tags_str = ", ".join(tags) if isinstance(tags, list) else ""

        salary_min = job.get("salary_min", 0)
        salary_max = job.get("salary_max", 0)

        raw_parts = [f"Title: {position}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if location:
            raw_parts.append(f"Location: {location}")
        if tags_str:
            raw_parts.append(f"Tags: {tags_str}")
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
        date_str = job.get("date", "")
        if date_str:
            with suppress(ValueError, TypeError):
                posted_at = datetime.fromisoformat(date_str).isoformat()

        permalink = job.get("url") or None

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": company_name or None,
            "posted_at": posted_at,
        }
