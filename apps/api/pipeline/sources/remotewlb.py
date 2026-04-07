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


REPO = "RemoteWLB/remote-jobs"
GITHUB_API = "https://api.github.com/repos"
RAW_BASE = "https://raw.githubusercontent.com"

CATEGORIES = [
    "Python",
    "React",
    "Nodejs",
    "Golang",
    "Java",
    "PHP",
    "Vue",
    "C#",
    "Nontech",
    "Others",
]

MAX_MONTHS = 2


@register_source
class RemotewlbService(BaseSource):
    """RemoteWLB source using the RemoteWLB/remote-jobs GitHub repo.

    Service details:
        - Data source: GitHub repo RemoteWLB/remote-jobs
        - Structure: jobs/{category}/{YYYY-MM}/{job-slug}/README.md
        - Categories: Python, React, Nodejs, Golang, Java, PHP, Vue, C#,
          Nontech, Others
        - Each README.md contains title (markdown link), salary/location line,
          and description section
        - Uses GitHub API to list directories, then fetches each README.md

    Fetch strategies (selected via sub_source 'type' in DB):
        - "category": sub_source.name = category folder name (e.g., "Python", "React")
                      Fetches jobs from a specific category.
        - "browse":   sub_source.name = ignored (fetches all categories)

    Scalability notes:
        - Max 2 months of data fetched to keep requests manageable
        - Multiple API calls per category (list months, list jobs, fetch READMEs)
        - GitHub API rate limit: 60 requests/hour unauthenticated
    """

    def get_source_name(self) -> str:
        return "remotewlb"

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

                categories = [name] if sub_type == "category" else CATEGORIES

                for cat in categories:
                    fetched = await self._fetch_category(client, cat, since)
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
        months = await self._list_months(client, category)
        if not months:
            return []

        months = months[:MAX_MONTHS]

        posts: list[RawPostData] = []
        for month in months:
            job_slugs = await self._list_jobs(client, category, month)
            for slug in job_slugs:
                post = await self._fetch_readme(client, category, month, slug)
                if post is None:
                    continue

                if since and post.get("posted_at"):
                    with suppress(ValueError, TypeError):
                        posted = datetime.fromisoformat(post["posted_at"])
                        if posted < since:
                            continue

                posts.append(post)

        return posts

    async def _list_months(
        self,
        client: httpx.AsyncClient,
        category: str,
    ) -> list[str]:
        resp = await client.get(
            f"{GITHUB_API}/{REPO}/contents/jobs/{category}",
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        if resp.status_code != 200:
            return []

        entries = resp.json()
        if not isinstance(entries, list):
            return []

        months: list[str] = []
        for entry in entries:
            if isinstance(entry, dict) and entry.get("type") == "dir":
                name = entry.get("name", "")
                if name:
                    months.append(name)

        months.sort(reverse=True)
        return months

    async def _list_jobs(
        self,
        client: httpx.AsyncClient,
        category: str,
        month: str,
    ) -> list[str]:
        resp = await client.get(
            f"{GITHUB_API}/{REPO}/contents/jobs/{category}/{month}",
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        if resp.status_code != 200:
            return []

        entries = resp.json()
        if not isinstance(entries, list):
            return []

        slugs: list[str] = []
        for entry in entries:
            if isinstance(entry, dict) and entry.get("type") == "dir":
                name = entry.get("name", "")
                if name:
                    slugs.append(name)

        return slugs

    async def _fetch_readme(
        self,
        client: httpx.AsyncClient,
        category: str,
        month: str,
        slug: str,
    ) -> RawPostData | None:
        resp = await client.get(
            f"{RAW_BASE}/{REPO}/main/jobs/{category}/{month}/{slug}/README.md"
        )
        if resp.status_code != 200:
            return None

        content = resp.text
        return self._parse_readme(content, category, month, slug)

    def _parse_readme(
        self,
        content: str,
        category: str,
        month: str,
        slug: str,
    ) -> RawPostData | None:
        external_id = f"wlb_{category}_{month}_{slug}"

        title_match = re.search(r"#\s*\[([^\]]+)\]\(([^)]+)\)", content)
        if not title_match:
            return None

        title = title_match.group(1).strip()
        url = title_match.group(2).strip()

        salary_str = ""
        location_str = ""
        salary_loc_match = re.search(
            r"[#]+\s*[^\n]*💰\s*([^\n]*?)[\s]*🌎\s*([^\n]*)", content
        )
        if salary_loc_match:
            salary_str = salary_loc_match.group(1).strip()
            location_str = salary_loc_match.group(2).strip()
        else:
            salary_match = re.search(r"[#]+\s*[^\n]*💰\s*([^\n]*)", content)
            if salary_match:
                salary_str = salary_match.group(1).strip()

        description = ""
        desc_match = re.search(r"##\s*Description\s*\n(.*)", content, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()

        raw_parts = [f"Title: {title}"]
        if salary_str:
            raw_parts.append(f"Salary: {salary_str}")
        if location_str:
            raw_parts.append(f"Location: {location_str}")
        raw_parts.append(f"Category: {category}")
        if description:
            raw_parts.append(f"\n{description}")

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": url or None,
            "author": None,
            "posted_at": None,
        }
