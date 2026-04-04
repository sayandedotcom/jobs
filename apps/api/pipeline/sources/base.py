from abc import ABC, abstractmethod
from datetime import datetime

from pipeline.state import RawPostData


class BaseSource(ABC):
    @abstractmethod
    async def fetch_new_posts(
        self, sub_sources: list[str], since: datetime | None = None
    ) -> list[RawPostData]: ...

    @abstractmethod
    def get_source_name(self) -> str: ...
