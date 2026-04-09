from datetime import datetime

import httpx
from pipeline.sources.base import BaseSource, _derive_title, _truncate_title
from pipeline.sources.hackernews.algolia import fetch_whoishiring
from pipeline.sources.hackernews.constants import HITS_PER_PAGE
from pipeline.sources.hackernews.firebase import fetch_jobstories
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


@register_source
class HackerNewsService(BaseSource):
    def get_source_name(self) -> str:
        return "hackernews"

    def skip_keyword_filter(self) -> bool:
        return True

    def use_embedding_dedup(self) -> bool:
        return False

    def build_listing_payload(self, post: RawPostData, item: dict) -> dict:
        metadata = dict(post.get("metadata") or {})
        header_line = _coerce_string(metadata.get("headerLine")) or _derive_title(
            post["raw_content"]
        )
        if post.get("author") and not metadata.get("hnAuthor"):
            metadata["hnAuthor"] = post["author"]
        metadata["headerLine"] = header_line

        return {
            "title": _truncate_title(header_line),
            "company": post.get("author") or "Unknown",
            "description": post["raw_content"],
            "location": None,
            "salary": None,
            "url": post.get("permalink"),
            "jobType": None,
            "applyUrl": None,
            "embeddingText": item.get("embedding_text"),
            "metadata": metadata,
        }

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
                sub_type = sub.get("type", "whoishiring")

                if sub_type == "jobstories":
                    fetched = await fetch_jobstories(client, since)
                else:
                    fetched = await fetch_whoishiring(
                        client, name, since, HITS_PER_PAGE
                    )

                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        return posts


def _coerce_string(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None
