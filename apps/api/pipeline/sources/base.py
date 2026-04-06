from abc import ABC, abstractmethod
from datetime import datetime

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
