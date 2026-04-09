import xml.etree.ElementTree as ET
from contextlib import suppress
from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.sources.utils import html_to_plain
from pipeline.state import RawPostData


def _parse_rss_items(xml_text: str) -> list[dict]:
    """Parse job items from a Teamtailor RSS feed.

    Extracts title, description, link, guid, pubDate, department, role,
    remote status, and locations from each <item> element.
    """
    root = ET.fromstring(xml_text)
    items: list[dict] = []

    for item in root.iter("item"):
        entry: dict = {}

        title_el = item.find("title")
        if title_el is not None and title_el.text:
            entry["title"] = title_el.text

        desc_el = item.find("description")
        if desc_el is not None and desc_el.text:
            entry["description"] = desc_el.text

        link_el = item.find("link")
        if link_el is not None and link_el.text:
            entry["link"] = link_el.text

        guid_el = item.find("guid")
        if guid_el is not None and guid_el.text:
            entry["guid"] = guid_el.text

        pub_el = item.find("pubDate")
        if pub_el is not None and pub_el.text:
            entry["pubDate"] = pub_el.text

        dept_el = item.find("{https://teamtailor.com/locations}department")
        if dept_el is not None and dept_el.text:
            entry["department"] = dept_el.text

        role_el = item.find("{https://teamtailor.com/locations}role")
        if role_el is not None and role_el.text:
            entry["role"] = role_el.text

        remote_el = item.find("remoteStatus")
        if remote_el is not None and remote_el.text:
            entry["remoteStatus"] = remote_el.text

        locations: list[dict] = []
        ns = {"tt": "https://teamtailor.com/locations"}
        for loc_el in item.findall("tt:locations/tt:location", ns):
            loc: dict = {}
            for field in ("city", "country"):
                field_el = loc_el.find(f"{{https://teamtailor.com/locations}}{field}")
                if field_el is not None and field_el.text:
                    loc[field] = field_el.text
            if loc:
                locations.append(loc)
        entry["locations"] = locations

        items.append(entry)

    return items


@register_source
class TeamtailorService(BaseSource):
    """Teamtailor job board source using the public RSS feed.

    Service details:
        - Uses the public RSS feed served by each company's Teamtailor site:
            https://{company}.teamtailor.com/jobs.rss
        - No API key required (public RSS feeds)
        - Each company has a unique subdomain slug (e.g., "spotify", "klarna")
        - RSS includes full HTML description, department, role, locations

    Fetch strategies (selected via sub_source 'type' in DB):
        - "board": sub_source.name = company subdomain slug (e.g., "spotify", "klarna")
                   Fetches all active jobs from that company's Teamtailor board.

    Scalability notes:
        - The RSS feed returns all active jobs in a single request (no pagination)
        - Each company board is fetched independently
        - httpx.AsyncClient is created per fetch call and properly closed
    """

    RSS_PATH = "/jobs.rss"

    def get_source_name(self) -> str:
        return "teamtailor"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        """Fetch jobs from Teamtailor boards specified in sub_sources.

        Args:
            sub_sources: List of dicts with 'name' and 'type' keys, e.g.:
                         [{'name': 'spotify', 'type': 'board'},
                          {'name': 'klarna', 'type': 'board'}]
            since:       Only return jobs published after this timestamp.

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
        """Fetch all active jobs from a company's Teamtailor RSS feed."""
        resp = await client.get(
            f"https://{slug}.teamtailor.com{self.RSS_PATH}",
            headers={"Accept": "application/rss+xml, application/xml, text/xml"},
        )
        if resp.status_code != 200:
            return []

        try:
            items = _parse_rss_items(resp.text)
        except ET.ParseError:
            return []

        posts: list[RawPostData] = []

        for item in items:
            guid = item.get("guid", "")
            if not guid:
                continue

            external_id = f"tt_{slug}_{guid}"

            pub_date = None
            pub_date_str = item.get("pubDate", "")
            if pub_date_str:
                for fmt in (
                    "%a, %d %b %Y %H:%M:%S %z",
                    "%a, %d %b %Y %H:%M:%S %Z",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%SZ",
                ):
                    with suppress(ValueError):
                        pub_date = datetime.strptime(pub_date_str, fmt)
                        break

            if since and pub_date and pub_date < since:
                continue

            title = item.get("title", "")
            description_html = item.get("description", "")
            description = html_to_plain(description_html) if description_html else ""
            department = item.get("department", "")
            remote_status = item.get("remoteStatus", "")
            locations = item.get("locations", [])

            location_parts: list[str] = []
            for loc in locations:
                parts = [loc.get("city", ""), loc.get("country", "")]
                location_parts.append(", ".join(p for p in parts if p))
            location_str = " | ".join(location_parts)

            raw_parts = [f"Title: {title}"]
            raw_parts.append(f"Company: {slug}")
            if location_str:
                raw_parts.append(f"Location: {location_str}")
            if department:
                raw_parts.append(f"Department: {department}")
            if remote_status and remote_status != "none":
                raw_parts.append(f"Remote: {remote_status}")
            if description:
                raw_parts.append(f"\n{description}")

            posted_at = pub_date.isoformat() if pub_date else None
            permalink = item.get("link") or None

            posts.append(
                {
                    "external_id": external_id,
                    "raw_content": "\n".join(raw_parts),
                    "permalink": permalink,
                    "author": slug,
                    "posted_at": posted_at,
                    "metadata": {},
                }
            )

        return posts
