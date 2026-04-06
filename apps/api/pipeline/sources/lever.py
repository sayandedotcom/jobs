import re
from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


def _html_to_plain(html: str) -> str:
    """Strip HTML tags to get plain text from Lever job descriptions."""
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
class LeverService(BaseSource):
    """Lever job board source using the public postings API.

    Service details:
        - Uses the public Lever postings API:
            https://api.lever.co/v0/postings/{company}?mode=json
        - No API key required for public postings
        - Each company on Lever has a unique site name (e.g., "netflix", "kagi")

    Fetch strategies (selected via sub_source 'type' in DB):
        - "board": sub_source.name = company site name (e.g., "netflix", "kagi")
                   Fetches all active postings from that company's Lever board.

    Scalability notes:
        - The API returns all postings in a single response (no pagination)
        - Each company board is fetched independently
        - httpx.AsyncClient is created per fetch call and properly closed
    """

    API_BASE = "https://api.lever.co/v0/postings"

    def get_source_name(self) -> str:
        return "lever"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        """Fetch jobs from Lever boards specified in sub_sources.

        Args:
            sub_sources: List of dicts with 'name' and 'type' keys, e.g.:
                         [{'name': 'netflix', 'type': 'board'},
                          {'name': 'kagi', 'type': 'board'}]
            since:       Only return jobs created after this timestamp.

        Returns:
            Deduplicated list of RawPostData (deduped by external_id).
        """
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                company = sub["name"]
                fetched = await self._fetch_board(client, company, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_board(
        self,
        client: httpx.AsyncClient,
        company: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        """Fetch all active postings from a company's Lever board.

        Uses ?mode=json to get structured data with full descriptions.
        The Lever API returns all postings in a single request.
        """
        resp = await client.get(
            f"{self.API_BASE}/{company}",
            params={"mode": "json"},
        )
        if resp.status_code != 200:
            return []

        data = resp.json()
        postings = data.get("postings", [])
        if not postings:
            return []

        posts: list[RawPostData] = []

        for posting in postings:
            posting_id = posting.get("id", "")
            if not posting_id:
                continue

            external_id = f"lever_{company}_{posting_id}"

            created_at = None
            created_at_str = posting.get("createdAt", "")
            if created_at_str:
                with suppress(ValueError, TypeError):
                    created_at = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )

            if since and created_at and created_at < since:
                continue

            title = posting.get("text", "")
            description_html = posting.get("description", "")
            description = _html_to_plain(description_html) if description_html else ""
            description_plain = posting.get("descriptionPlain", "") or description

            categories = posting.get("categories", {})
            location = ""
            team = ""
            commitment = ""
            if isinstance(categories, dict):
                location = categories.get("location", "")
                team = categories.get("team", "")
                commitment = categories.get("commitment", "")

            raw_parts = [f"Title: {title}"]
            raw_parts.append(f"Company: {company}")
            if location:
                raw_parts.append(f"Location: {location}")
            if team:
                raw_parts.append(f"Team: {team}")
            if commitment:
                raw_parts.append(f"Commitment: {commitment}")
            if description_plain:
                raw_parts.append(f"\n{description_plain}")

            posted_at = created_at.isoformat() if created_at else None
            permalink = posting.get("hostedUrl") or None
            apply_url = posting.get("applyUrl") or None

            posts.append(
                {
                    "external_id": external_id,
                    "raw_content": "\n".join(raw_parts),
                    "permalink": permalink or apply_url,
                    "author": company,
                    "posted_at": posted_at,
                }
            )

        return posts
