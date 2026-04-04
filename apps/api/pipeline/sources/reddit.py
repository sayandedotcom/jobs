from datetime import datetime, UTC

import asyncpraw
from pipeline.sources.base import BaseSource
from pipeline.state import RawPostData


class RedditSource(BaseSource):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent

    def get_source_name(self) -> str:
        return "reddit"

    async def fetch_new_posts(
        self, sub_sources: list[str], since: datetime | None = None
    ) -> list[RawPostData]:
        reddit = asyncpraw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )
        posts: list[RawPostData] = []
        try:
            for subreddit_name in sub_sources:
                subreddit = await reddit.subreddit(subreddit_name)
                async for submission in subreddit.new(limit=100):
                    created_at = datetime.fromtimestamp(submission.created_utc, tz=UTC)
                    if since and created_at < since:
                        continue
                    content = self._build_content(submission)
                    posts.append(
                        {
                            "external_id": f"reddit_{submission.id}",
                            "raw_content": content,
                            "permalink": f"https://reddit.com{submission.permalink}",
                            "author": str(submission.author)
                            if submission.author
                            else None,
                            "posted_at": created_at.isoformat(),
                        }
                    )
        finally:
            await reddit.close()
        return posts

    def _build_content(self, submission) -> str:
        parts = [f"Title: {submission.title}"]
        if hasattr(submission, "selftext") and submission.selftext:
            parts.append(f"Body: {submission.selftext}")
        if hasattr(submission, "link_flair_text") and submission.link_flair_text:
            parts.append(f"Flair: {submission.link_flair_text}")
        if hasattr(submission, "url") and submission.url:
            parts.append(f"URL: {submission.url}")
        return "\n\n".join(parts)
