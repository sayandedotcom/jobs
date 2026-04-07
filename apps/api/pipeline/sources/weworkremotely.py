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
    for tag in ("</p>", "</li>", "</div>", "<br>", "<br/>>", "<br />"):
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


RSS_FEEDS: dict[str, str] = {
    "programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "design": "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "devops-sysadmin": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "product": "https://weworkremotely.com/categories/remote-product-jobs.rss",
    "customer-support": "https://weworkremotely.com/categories/remote-customer-support-jobs.rss",
    "sales-marketing": "https://weworkremotely.com/categories/remote-sales-marketing-jobs.rss",
    "copywriting": "https://weworkremotely.com/categories/remote-copywriting-jobs.rss",
    "finance-legal": "https://weworkremotely.com/categories/remote-finance-legal-jobs.rss",
    "management-executive": "https://weworkremotely.com/categories/remote-management-executive-jobs.rss",
    "all": "https://weworkremotely.com/remote-jobs.rss",
}


@register_source
class WeworkremotelyService(BaseSource):
    """WeWorkRemotely remote job board source using the public RSS feeds.

    Service details:
        - Category-specific RSS feeds at weworkremotely.com
        - No API key required (free RSS access)
        - Each RSS feed returns all active jobs in that category
        - Title format: "{Company}: {Job Title}"
        - Full HTML description included in each item

    Fetch strategies (selected via sub_source 'type' in DB):
        - "category": sub_source.name = category slug (e.g., "programming", "design")
        - "browse":   sub_source.name = ignored (fetches all categories)

    Available categories: programming, design, devops-sysadmin, product,
    customer-support, sales-marketing, copywriting, finance-legal,
    management-executive, all
    """

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
            for sub in sub_sources:
                name = sub["name"]
                sub_type = sub.get("type", "browse")

                if sub_type == "category" and name in RSS_FEEDS:
                    feeds = {name: RSS_FEEDS[name]}
                else:
                    feeds = RSS_FEEDS

                for cat, url in feeds.items():
                    fetched = await self._fetch_feed(client, cat, url, since)
                    for post in fetched:
                        if post["external_id"] not in seen_ids:
                            seen_ids.add(post["external_id"])
                            posts.append(post)
        return posts

    async def _fetch_feed(
        self,
        client: httpx.AsyncClient,
        category: str,
        url: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        resp = await client.get(
            url,
            headers={"Accept": "application/rss+xml, application/xml, text/xml"},
        )
        if resp.status_code != 200:
            return []

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError:
            return []

        posts: list[RawPostData] = []

        for item in root.iter("item"):
            guid_el = item.find("guid")
            guid = guid_el.text if guid_el is not None and guid_el.text else ""
            if not guid:
                continue

            external_id = f"wwr_{category}_{guid}"

            pub_date = None
            pub_el = item.find("pubDate")
            if pub_el is not None and pub_el.text:
                for fmt in (
                    "%a, %d %b %Y %H:%M:%S %z",
                    "%a, %d %b %Y %H:%M:%S %Z",
                    "%Y-%m-%dT%H:%M:%S%z",
                    "%Y-%m-%dT%H:%M:%SZ",
                ):
                    with suppress(ValueError):
                        pub_date = datetime.strptime(pub_el.text, fmt)
                        break

            if since and pub_date and pub_date < since:
                continue

            title_el = item.find("title")
            full_title = title_el.text if title_el is not None and title_el.text else ""

            company_name = ""
            position = full_title
            if ": " in full_title:
                company_name, position = full_title.split(": ", 1)

            region_el = item.find("region")
            region = region_el.text if region_el is not None and region_el.text else ""

            cat_el = item.find("category")
            job_category = cat_el.text if cat_el is not None and cat_el.text else ""

            desc_el = item.find("description")
            description_html = (
                desc_el.text if desc_el is not None and desc_el.text else ""
            )
            description = _html_to_plain(description_html) if description_html else ""

            link_el = item.find("link")
            link = link_el.text if link_el is not None and link_el.text else ""

            raw_parts = [f"Title: {position}"]
            if company_name:
                raw_parts.append(f"Company: {company_name}")
            if region:
                raw_parts.append(f"Region: {region}")
            if job_category:
                raw_parts.append(f"Category: {job_category}")
            if description:
                raw_parts.append(f"\n{description}")

            posted_at = pub_date.isoformat() if pub_date else None
            permalink = link or guid

            posts.append(
                {
                    "external_id": external_id,
                    "raw_content": "\n".join(raw_parts),
                    "permalink": permalink,
                    "author": company_name or None,
                    "posted_at": posted_at,
                }
            )

        return posts
