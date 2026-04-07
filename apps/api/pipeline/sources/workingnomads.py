import re
import xml.etree.ElementTree as ET
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


CATEGORIES = [
    "dev",
    "design",
    "marketing",
    "sales",
    "management",
    "customer-service",
    "finance",
    "sysadmin",
    "writing",
    "education",
    "consulting",
    "legal",
    "healthcare",
    "hr",
    "administration",
]


def _parse_rss_items(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items: list[dict] = []

    for item in root.iter("item"):
        entry: dict = {}

        title_el = item.find("title")
        if title_el is not None and title_el.text:
            entry["title"] = title_el.text

        link_el = item.find("link")
        if link_el is not None and link_el.text:
            entry["link"] = link_el.text

        desc_el = item.find("description")
        if desc_el is not None and desc_el.text:
            entry["description"] = desc_el.text

        pub_el = item.find("pubDate")
        if pub_el is not None and pub_el.text:
            entry["pubDate"] = pub_el.text

        guid_el = item.find("guid")
        if guid_el is not None and guid_el.text:
            entry["guid"] = guid_el.text

        items.append(entry)

    return items


@register_source
class WorkingnomadsService(BaseSource):
    """Working Nomads remote job board source using the RSS feed.

    Service details:
        - RSS feed: https://www.workingnomads.com/api/extras/jobs-rss.php?category={cat}
        - No API key required
        - Multiple job categories available
        - RSS items include title ("{position} at {company}"), description (HTML), link

    Fetch strategies (selected via sub_source 'type' in DB):
        - "category": sub_source.name = category slug (e.g., "dev", "design")
                      Fetches jobs from a specific category RSS feed.
        - "browse":   sub_source.name = ignored (fetches all categories)

    Categories: dev, design, marketing, sales, management, customer-service,
    finance, sysadmin, writing, education, consulting, legal, healthcare,
    hr, administration
    """

    RSS_BASE = "https://www.workingnomads.com/api/extras/jobs-rss.php"

    def get_source_name(self) -> str:
        return "workingnomads"

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
        resp = await client.get(
            self.RSS_BASE,
            params={"category": category},
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

            external_id = f"wn_{guid}"

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
            description = _html_to_plain(description_html) if description_html else ""

            raw_parts = [f"Title: {title}"]
            raw_parts.append(f"Category: {category}")
            if description:
                raw_parts.append(f"\n{description}")

            posted_at = pub_date.isoformat() if pub_date else None
            permalink = item.get("link") or None

            posts.append(
                {
                    "external_id": external_id,
                    "raw_content": "\n".join(raw_parts),
                    "permalink": permalink,
                    "author": None,
                    "posted_at": posted_at,
                    "metadata": {},
                }
            )

        return posts
