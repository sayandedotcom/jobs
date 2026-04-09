from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipeline.state import RawPostData


class BaseSource(ABC):
    """Abstract base for all job-fetching sources (Reddit, LinkedIn, Indeed, etc.).

    To add a new source:
        1. Create a new file in pipeline/sources/ (e.g., linkedin.py)
        2. Subclass BaseSource, implement fetch_new_posts() and get_source_name()
        3. Decorate the class with @register_source
        4. Import the module in pipeline/sources/__init__.py to trigger registration
        5. Add the source's constructor kwargs to SOURCE_CONFIGS in source_configs.py
        6. Add any required API keys/env vars to core/config.py Settings

    The registry pattern (pipeline/sources/registry.py) handles auto-discovery:
        - @register_source decorator registers the class by its source name at import time
        - get_source(name, **kwargs) factory instantiates the right class at runtime
        - SOURCE_CONFIGS provides the constructor kwargs from environment variables

    Each source maps to a row in the 'sources' DB table, and its sub-sources
    (e.g., subreddits for Reddit, job boards for Indeed) are stored in 'sub_sources'.

    Behavioral hooks (override in subclasses for custom pipeline behavior):
        - skip_keyword_filter: Return True to bypass keyword filtering (e.g., HN)
        - use_embedding_dedup: Return False to use exact-only dedup (e.g., HN)
        - build_listing_payload: Customize how post data maps to a DB listing row
    """

    @abstractmethod
    async def fetch_new_posts(
        self, sub_sources: list[dict], since: datetime | None = None
    ) -> list[RawPostData]:
        """Fetch raw posts from the external source.

        Args:
            sub_sources: List of dicts with 'name' and 'type' keys, e.g.:
                         [{'name': 'forhire', 'type': 'subreddit'},
                          {'name': 'hiring remote', 'type': 'search'}]
                         The 'type' field determines the fetch strategy within the source.
            since:       Only return posts newer than this timestamp (incremental fetch).

        Returns:
            List of RawPostData dicts with external_id prefixed by "<source>_".
        """
        ...

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the unique identifier for this source (e.g., 'reddit', 'linkedin').

        This name must match the 'name' column in the 'sources' DB table
        and the key in SOURCE_CONFIGS.
        """
        ...

    def skip_keyword_filter(self) -> bool:
        """Whether to bypass keyword-based filtering for this source.

        Override to return True for sources where all posts are known to be job-related
        (e.g., HN "Who is Hiring?" threads where every comment is a job post).
        """
        return False

    def use_embedding_dedup(self) -> bool:
        """Whether to use embedding-based fuzzy dedup for this source.

        Override to return False for sources that already have unique external IDs
        and don't benefit from expensive embedding comparisons.
        """
        return True

    def build_listing_payload(self, post: RawPostData, item: dict) -> dict:
        """Build the listing DB row payload from a raw post.

        Override to customize title derivation, metadata enrichment, or field mapping.
        Default implementation derives the title from the first line of raw_content.

        Args:
            post: The raw post data from the source.
            item: Dict with 'embedding_text' key from the dedup step.

        Returns:
            Dict with keys: title, company, description, location, salary, url,
            jobType, applyUrl, embeddingText, metadata.
        """
        metadata = dict(post.get("metadata") or {})
        return {
            "title": _derive_title(post["raw_content"]),
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


def _derive_title(raw_content: str) -> str:
    first_line = raw_content.split("\n", 1)[0].strip()
    if first_line.startswith("Title:"):
        first_line = first_line[len("Title:") :].strip()
    return _truncate_title(first_line or "Untitled")


def _truncate_title(value: str) -> str:
    if len(value) > 150:
        return value[:147] + "..."
    return value
