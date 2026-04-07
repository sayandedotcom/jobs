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


BLOG_CATEGORY_KEYWORDS = {
    "career",
    "career transitions",
    "career advice",
    "career development",
    "interview tips",
    "resume tips",
    "job search tips",
    "workplace culture",
}

JOB_ID_PATTERN = re.compile(r"/jobs/\d+|/job/\d+|\bid=\d+")


def _is_likely_job(item: dict) -> bool:
    guid = item.get("guid", "")
    if JOB_ID_PATTERN.search(guid):
        return True

    link = item.get("link", "")
    if JOB_ID_PATTERN.search(link):
        return True

    title = item.get("title", "").lower()
    if title.startswith("how to"):
        return False

    categories = item.get("categories", [])
    lower_cats = {c.lower() for c in categories} if categories else set()
    if lower_cats and lower_cats.issubset(BLOG_CATEGORY_KEYWORDS):
        return False

    return False


def _parse_rss_items(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items: list[dict] = []

    for item_el in root.iter("item"):
        entry: dict = {}

        title_el = item_el.find("title")
        if title_el is not None and title_el.text:
            entry["title"] = title_el.text

        link_el = item_el.find("link")
        if link_el is not None and link_el.text:
            entry["link"] = link_el.text

        desc_el = item_el.find("description")
        if desc_el is not None and desc_el.text:
            entry["description"] = desc_el.text

        pub_el = item_el.find("pubDate")
        if pub_el is not None and pub_el.text:
            entry["pubDate"] = pub_el.text

        guid_el = item_el.find("guid")
        if guid_el is not None and guid_el.text:
            entry["guid"] = guid_el.text

        categories: list[str] = []
        for cat_el in item_el.findall("category"):
            if cat_el.text:
                categories.append(cat_el.text)
        entry["categories"] = categories

        items.append(entry)

    return items


@register_source
class AuthenticjobsService(BaseSource):
    """Authentic Jobs RSS feed source.

    Service details:
        - RSS feed: https://authenticjobs.com/feed/
        - No API key required
        - NOTE: The RSS feed currently contains mostly blog posts rather than
          actual job listings. This source filters items to keep only those
          that appear to be job listings based on guid/link patterns and
          category analysis. Results may be empty if no job listings are present.

    Fetch strategies (selected via sub_source 'type' in DB):
        - "browse": sub_source.name = ignored (fetches all items from feed)
    """

    RSS_URL = "https://authenticjobs.com/feed/"

    def get_source_name(self) -> str:
        return "authenticjobs"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for _sub in sub_sources:
                fetched = await self._fetch_feed(client, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_feed(
        self,
        client: httpx.AsyncClient,
        since: datetime | None,
    ) -> list[RawPostData]:
        resp = await client.get(
            self.RSS_URL,
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
            if not _is_likely_job(item):
                continue

            guid = item.get("guid", "")
            if not guid:
                continue

            external_id = f"aj_{guid}"

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
