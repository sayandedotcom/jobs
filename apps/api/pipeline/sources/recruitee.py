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
class RecruiteeService(BaseSource):
    """Recruitee job board source using the public offers API.

    Service details:
        - Uses the Recruitee public offers API:
            https://{company_slug}.recruitee.com/api/offers
        - No API key required
        - Each company has a unique slug subdomain (e.g., "strv", "infobip")
        - Returns all active offers with full HTML descriptions

    Fetch strategies (selected via sub_source 'type' in DB):
        - "company": sub_source.name = company slug (e.g., "strv")
                     Fetches all active offers from that company's Recruitee board.

    Scalability notes:
        - Single request returns all offers (no pagination)
        - Each company board is fetched independently
        - httpx.AsyncClient is created per fetch call and properly closed
    """

    API_TEMPLATE = "https://{}.recruitee.com/api/offers"

    def get_source_name(self) -> str:
        return "recruitee"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for sub in sub_sources:
                slug = sub["name"]
                fetched = await self._fetch_company(client, slug, since)
                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts

    async def _fetch_company(
        self,
        client: httpx.AsyncClient,
        slug: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        resp = await client.get(self.API_TEMPLATE.format(slug))
        if resp.status_code != 200:
            return []

        data = resp.json()
        offers = data.get("offers", [])
        if not offers:
            return []

        posts: list[RawPostData] = []

        for offer in offers:
            post = self._parse_offer(offer, slug)
            if post is None:
                continue

            if since and post.get("posted_at"):
                with suppress(ValueError, TypeError):
                    posted = datetime.fromisoformat(post["posted_at"])
                    if posted < since:
                        continue

            posts.append(post)

        return posts

    def _parse_offer(self, offer: dict, slug: str) -> RawPostData | None:
        offer_id = offer.get("id", "")
        if not offer_id:
            return None

        external_id = f"rec_{offer_id}"

        title = offer.get("title", "")
        company_name = offer.get("company_name", "") or slug

        description_html = offer.get("description", "")
        description = _html_to_plain(description_html) if description_html else ""

        requirements_html = offer.get("requirements", "")
        requirements = _html_to_plain(requirements_html) if requirements_html else ""

        location = offer.get("location", "")
        city = offer.get("city", "")
        country = offer.get("country", "")
        remote = offer.get("remote", False)

        location_parts: list[str] = []
        for part in (city, location, country):
            if part:
                location_parts.append(part)
        location_str = ", ".join(location_parts)

        department = offer.get("department", "")
        employment_type = offer.get("employment_type_code", "")
        experience = offer.get("experience_code", "")

        salary = offer.get("salary", {})
        salary_str = ""
        if isinstance(salary, dict):
            salary_parts: list[str] = []
            salary_min = salary.get("min")
            salary_max = salary.get("max")
            currency = salary.get("currency", "")
            period = salary.get("period", "")
            if salary_min:
                salary_parts.append(str(salary_min))
            if salary_max:
                salary_parts.append(str(salary_max))
            if salary_parts:
                salary_str = "-".join(salary_parts)
                if currency:
                    salary_str = f"{salary_str} {currency}"
                if period:
                    salary_str = f"{salary_str} per {period}"

        tags = offer.get("tags") or []
        tags_str = ", ".join(tags) if isinstance(tags, list) else ""

        raw_parts = [f"Title: {title}"]
        if company_name:
            raw_parts.append(f"Company: {company_name}")
        if location_str:
            raw_parts.append(f"Location: {location_str}")
        if remote:
            raw_parts.append("Remote: Yes")
        if department:
            raw_parts.append(f"Department: {department}")
        if employment_type:
            raw_parts.append(f"Employment: {employment_type}")
        if experience:
            raw_parts.append(f"Experience: {experience}")
        if salary_str:
            raw_parts.append(f"Salary: {salary_str}")
        if tags_str:
            raw_parts.append(f"Tags: {tags_str}")
        if description:
            raw_parts.append(f"\n{description}")
        if requirements:
            raw_parts.append(f"\nRequirements:\n{requirements}")

        posted_at = None
        published_str = offer.get("published_at", "")
        if published_str:
            with suppress(ValueError, TypeError):
                posted_at = datetime.fromisoformat(
                    published_str.replace("Z", "+00:00")
                ).isoformat()

        permalink = offer.get("careers_url") or None

        return {
            "external_id": external_id,
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": company_name or slug,
            "posted_at": posted_at,
            "metadata": {},
        }
