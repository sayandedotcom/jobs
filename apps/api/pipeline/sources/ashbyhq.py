import re
from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


def _html_to_plain(html: str) -> str:
    """Strip HTML tags to get plain text from AshbyHQ job descriptions."""
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


def _extract_app_data(html: str) -> dict | None:
    """Extract and parse window.__appData JSON from AshbyHQ page HTML."""
    m = re.search(r"window\.__appData\s*=\s*(\{)", html)
    if not m:
        return None
    start = m.start(1)
    depth = 0
    for i in range(start, len(html)):
        if html[i] == "{":
            depth += 1
        elif html[i] == "}":
            depth -= 1
        if depth == 0:
            import json

            return json.loads(html[start : i + 1])
    return None


@register_source
class AshbyHQService(BaseSource):
    """AshbyHQ job board source using the hosted careers page.

    Service details:
        - Scrapes job data from AshbyHQ's hosted careers pages:
            https://jobs.ashbyhq.com/{companySlug}
        - No API key required (public job board pages)
        - Each company on AshbyHQ has a unique slug (e.g., "Ashby", "Vercel")
        - Job listings are server-side rendered into the HTML as JSON

    Fetch strategies (selected via sub_source 'type' in DB):
        - "board": sub_source.name = company slug (e.g., "Ashby", "Vercel")
                   Fetches all active postings from that company's board.
                   Optionally fetches full descriptions per posting.

    Scalability notes:
        - The listing page returns all postings in one request (no pagination)
        - Individual posting pages are fetched for full descriptions
        - httpx.AsyncClient is created per fetch call and properly closed
    """

    JOBS_BASE = "https://jobs.ashbyhq.com"

    def get_source_name(self) -> str:
        return "ashbyhq"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        """Fetch jobs from AshbyHQ boards specified in sub_sources.

        Args:
            sub_sources: List of dicts with 'name' and 'type' keys, e.g.:
                         [{'name': 'Ashby', 'type': 'board'},
                          {'name': 'Vercel', 'type': 'board'}]
            since:       Only return jobs updated after this timestamp.

        Returns:
            Deduplicated list of RawPostData (deduped by external_id).
        """
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                slug = sub["name"]
                fetched = await self._fetch_board(client, slug, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_board(
        self,
        client: httpx.AsyncClient,
        slug: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        """Fetch all active postings from a company's AshbyHQ board.

        Parses the server-side rendered JSON from the hosted job board page.
        Then fetches each individual posting for full description.
        """
        resp = await client.get(f"{self.JOBS_BASE}/{slug}")
        if resp.status_code != 200:
            return []

        app_data = _extract_app_data(resp.text)
        if not app_data:
            return []

        job_board = app_data.get("jobBoard", {})
        postings = job_board.get("jobPostings", [])
        if not postings:
            return []

        posts: list[RawPostData] = []

        for posting in postings:
            posting_id = posting.get("id", "")
            if not posting_id:
                continue

            external_id = f"ashby_{slug}_{posting_id}"

            updated_at = None
            updated_at_str = posting.get("updatedAt", "")
            if updated_at_str:
                with suppress(ValueError, TypeError):
                    updated_at = datetime.fromisoformat(
                        updated_at_str.replace("Z", "+00:00")
                    )

            if since and updated_at and updated_at < since:
                continue

            title = posting.get("title", "")
            location_name = posting.get("locationName", "")
            department = posting.get("departmentName", "")
            team = posting.get("teamName", "")
            workplace_type = posting.get("workplaceType", "")
            employment_type = posting.get("employmentType", "")
            compensation = posting.get("compensationTierSummary", "")

            description = await self._fetch_posting_description(
                client, slug, posting_id
            )

            raw_parts = [f"Title: {title}"]
            raw_parts.append(f"Company: {slug}")
            if location_name:
                raw_parts.append(f"Location: {location_name}")
            if department:
                raw_parts.append(f"Department: {department}")
            if team:
                raw_parts.append(f"Team: {team}")
            if workplace_type:
                raw_parts.append(f"Workplace: {workplace_type}")
            if employment_type:
                raw_parts.append(f"Employment: {employment_type}")
            if compensation:
                raw_parts.append(f"Compensation: {compensation}")
            if description:
                raw_parts.append(f"\n{description}")

            posted_at = updated_at.isoformat() if updated_at else None
            permalink = f"{self.JOBS_BASE}/{slug}/{posting_id}"

            posts.append(
                {
                    "external_id": external_id,
                    "raw_content": "\n".join(raw_parts),
                    "permalink": permalink,
                    "author": slug,
                    "posted_at": posted_at,
                }
            )

        return posts

    async def _fetch_posting_description(
        self,
        client: httpx.AsyncClient,
        slug: str,
        posting_id: str,
    ) -> str:
        """Fetch the full description for an individual posting.

        The listing page only has metadata; the individual posting page
        contains descriptionHtml and descriptionPlainText.
        """
        resp = await client.get(f"{self.JOBS_BASE}/{slug}/{posting_id}")
        if resp.status_code != 200:
            return ""

        app_data = _extract_app_data(resp.text)
        if not app_data:
            return ""

        posting = app_data.get("posting", {})
        if not posting:
            return ""

        plain = posting.get("descriptionPlainText", "")
        if plain:
            return plain

        html = posting.get("descriptionHtml", "")
        if html:
            return _html_to_plain(html)

        return ""
