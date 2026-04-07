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
class RemotiveService(BaseSource):
    """Remotive remote job board source using the public JSON API.

    Service details:
        - https://remotive.com/api/remote-jobs
        - No API key required
        - Supports ?search={query}&category={cat}&limit={n} filters
        - Each job includes HTML description, company, tags, salary, location
        - 24hr delay on job data; max ~4 requests/day recommended

    Fetch strategies (selected via sub_source 'type' in DB):
        - "category": sub_source.name = category (e.g., "Software Development")
        - "search":   sub_source.name = search query
        - "browse":   sub_source.name = ignored (fetches all jobs)
    """

    API_URL = "https://remotive.com/api/remote-jobs"

    def get_source_name(self) -> str:
        return "remotive"

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

                params: dict = {"limit": 50}
                if sub_type == "category":
                    params["category"] = name
                elif sub_type == "search":
                    params["search"] = name

                fetched = await self._fetch(client, params, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch(
        self,
        client: httpx.AsyncClient,
        params: dict,
        since: datetime | None,
    ) -> list[RawPostData]:
        resp = await client.get(self.API_URL, params=params)
        if resp.status_code != 200:
            return []

        data = resp.json()
        jobs = data.get("jobs", [])
        if not jobs:
            return []

        posts: list[RawPostData] = []
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

        return posts

    def _parse_job(self, job: dict) -> RawPostData | None:
        job_id = job.get("id")
        if not job_id:
            return None

        external_id = f"remotive_{job_id}"

        title = job.get("title", "")
        company_name = job.get("company_name", "")
        description_html = job.get("description", "")
        description = _html_to_plain(description_html) if description_html else ""

        location = job.get("candidate_required_location", "")
        category = job.get("category", "")
        job_type = job.get("job_type", "")
        salary = job.get("salary", "")
        tags = job.get("tags") or []
        tags_str = ", ".join(tags) if isinstance(tags, list) else ""

        raw_parts = [f"Title: {title}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if location:
            raw_parts.append(f"Location: {location}")
        if category:
            raw_parts.append(f"Category: {category}")
        if job_type:
            raw_parts.append(f"Type: {job_type}")
        if salary:
            raw_parts.append(f"Salary: {salary}")
        if tags_str:
            raw_parts.append(f"Tags: {tags_str}")
        if description:
            raw_parts.append(f"\n{description}")

        posted_at = None
        pub_str = job.get("publication_date", "")
        if pub_str:
            with suppress(ValueError, TypeError):
                posted_at = datetime.fromisoformat(pub_str).isoformat()

        permalink = job.get("url") or None

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": company_name or None,
            "posted_at": posted_at,
            "metadata": {},
        }
