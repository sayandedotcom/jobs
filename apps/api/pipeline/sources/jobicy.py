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
class JobicyService(BaseSource):
    """Jobicy remote job board source using the public JSON API.

    Service details:
        - https://jobicy.com/api/v2/remote-jobs
        - No API key required
        - Params: count=50, search={query}, page={n}
        - Each job includes HTML description, company, industry, salary info

    Fetch strategies (selected via sub_source 'type' in DB):
        - "browse": sub_source.name = ignored (fetches all jobs)
        - "search": sub_source.name = search query
    """

    API_URL = "https://jobicy.com/api/v2/remote-jobs"
    PAGE_SIZE = 50
    MAX_PAGES = 3

    def get_source_name(self) -> str:
        return "jobicy"

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
        page = 1

        for _ in range(self.MAX_PAGES):
            params: dict = {"count": self.PAGE_SIZE, "page": page}
            if search_query:
                params["search"] = search_query

            resp = await client.get(self.API_URL, params=params)
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

            if len(jobs) < self.PAGE_SIZE:
                break

            page += 1

        return posts

    def _parse_job(self, job: dict) -> RawPostData | None:
        job_id = job.get("id", "")
        if not job_id:
            return None

        external_id = f"jobicy_{job_id}"

        title = job.get("jobTitle", "")
        company_name = job.get("companyName", "")
        description_html = job.get("jobDescription", "")
        description = _html_to_plain(description_html) if description_html else ""
        excerpt = job.get("jobExcerpt", "")

        job_industry = job.get("jobIndustry") or []
        industry_str = ", ".join(job_industry) if isinstance(job_industry, list) else ""

        job_type = job.get("jobType") or []
        job_type_str = ", ".join(job_type) if isinstance(job_type, list) else ""

        job_geo = job.get("jobGeo", "")
        job_level = job.get("jobLevel", "")

        salary_min = job.get("salaryMin", 0)
        salary_max = job.get("salaryMax", 0)
        salary_currency = job.get("salaryCurrency", "")
        salary_period = job.get("salaryPeriod", "")

        raw_parts = [f"Title: {title}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if job_geo:
            raw_parts.append(f"Location: {job_geo}")
        if industry_str:
            raw_parts.append(f"Industry: {industry_str}")
        if job_type_str:
            raw_parts.append(f"Job Type: {job_type_str}")
        if job_level:
            raw_parts.append(f"Level: {job_level}")
        if salary_min or salary_max:
            salary_parts: list[str] = []
            if salary_min:
                salary_parts.append(str(salary_min))
            if salary_max:
                salary_parts.append(str(salary_max))
            salary_range = "-".join(salary_parts)
            if salary_currency:
                salary_range = f"{salary_range} {salary_currency}"
            if salary_period:
                salary_range = f"{salary_range} per {salary_period}"
            raw_parts.append(f"Salary: {salary_range}")
        if excerpt:
            raw_parts.append(f"\n{excerpt}")
        if description:
            raw_parts.append(f"\n{description}")

        posted_at = None
        pub_str = job.get("pubDate", "")
        if pub_str:
            with suppress(ValueError, TypeError):
                posted_at = datetime.fromisoformat(
                    pub_str.replace("Z", "+00:00")
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
