from __future__ import annotations

from datetime import datetime

from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


@register_source
class SmashingjobsService(BaseSource):
    """Smashing Magazine Jobs source (placeholder).

    Service details:
        - Jobs are rendered in HTML at:
            https://www.smashingmagazine.com/jobs/
        - No RSS feed or JSON API available
        - HTML scraping would be required to extract job listings
        - This source currently returns empty results

    Fetch strategies (selected via sub_source 'type' in DB):
        - "browse": sub_source.name = ignored (returns empty list)
    """

    def get_source_name(self) -> str:
        return "smashingjobs"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        return []
