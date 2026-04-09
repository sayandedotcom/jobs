from datetime import datetime, UTC

import asyncpraw
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


@register_source
class RedditService(BaseSource):
    """Unified Reddit service with multiple fetch strategies.

    Service details:
        - Uses the Reddit API (OAuth2) through asyncpraw
        - Requires a registered Reddit app: https://www.reddit.com/prefs/apps
        - API credentials: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
        - Rate limits: Reddit allows ~60 requests/min for OAuth2 apps

    Fetch strategies (selected via sub_source 'type' in DB):
        - "subreddit": Fetches newest posts from configured subreddits
                       sub_source.name = subreddit name (e.g., 'forhire', 'remotejs')
        - "search":    Executes Reddit search queries across all subreddits
                       sub_source.name = search query (e.g., 'hiring remote engineer')

    Scalability notes:
        - Each subreddit/query is a separate API call (sequential)
        - For many sub_sources, consider parallelizing with asyncio.gather()
        - Reddit API pagination limit is 100 items per request
        - No retry/backoff logic currently — wrapped in try/finally only for cleanup
    """

    SUBREDDIT_FETCH_LIMIT = 100
    SEARCH_FETCH_LIMIT = 100
    SEARCH_SORT = "new"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
    ):
        # Reddit OAuth2 credentials from SOURCE_CONFIGS (backed by env vars)
        # Create an app at https://www.reddit.com/prefs/apps → "script" type
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent

    def get_source_name(self) -> str:
        # Must match the key in SOURCE_CONFIGS and the 'name' column in 'sources' DB table
        return "reddit"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        """Dispatch to the appropriate fetch strategy based on sub_source type.

        Args:
            sub_sources: List of dicts with 'name' and 'type' keys, e.g.:
                         [{'name': 'forhire', 'type': 'subreddit'},
                          {'name': 'hiring remote', 'type': 'search'}]
            since:       Only return posts newer than this timestamp (incremental fetch).

        Returns:
            Deduplicated list of RawPostData (deduped by external_id).
        """
        reddit = asyncpraw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )
        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        try:
            for sub in sub_sources:
                name = sub["name"]
                sub_type = sub.get("type", "subreddit")

                if sub_type == "search":
                    fetched = await self._fetch_by_search(reddit, name, since)
                else:
                    fetched = await self._fetch_by_subreddit(reddit, name, since)

                for post in fetched:
                    if post["external_id"] not in seen_ids:
                        seen_ids.add(post["external_id"])
                        posts.append(post)
        finally:
            # Always close the Reddit client to release the HTTP session
            await reddit.close()
        return posts

    async def _fetch_by_subreddit(
        self, reddit: asyncpraw.Reddit, subreddit_name: str, since: datetime | None
    ) -> list[RawPostData]:
        """Fetch newest posts from a specific subreddit.

        Uses the subreddit.new() endpoint which returns up to SUBREDDIT_FETCH_LIMIT
        of the most recent submissions in chronological order.
        """
        posts: list[RawPostData] = []
        subreddit = await reddit.subreddit(subreddit_name)
        async for submission in subreddit.new(limit=self.SUBREDDIT_FETCH_LIMIT):
            created_at = datetime.fromtimestamp(submission.created_utc, tz=UTC)
            # Skip posts older than the last successful scan (incremental fetch)
            if since and created_at < since:
                continue
            content = self._build_content(submission)
            posts.append(
                {
                    "external_id": f"reddit_{submission.id}",
                    "raw_content": content,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "author": str(submission.author) if submission.author else None,
                    "posted_at": created_at.isoformat(),
                    "metadata": {
                        "subreddit": subreddit_name,
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "flair": submission.link_flair_text
                        if hasattr(submission, "link_flair_text")
                        and submission.link_flair_text
                        else None,
                        "title": submission.title,
                    },
                }
            )
        return posts

    async def _fetch_by_search(
        self, reddit: asyncpraw.Reddit, query: str, since: datetime | None
    ) -> list[RawPostData]:
        """Execute a Reddit search query across all subreddits.

        Uses reddit.search() with SEARCH_SORT='new' and SEARCH_FETCH_LIMIT.
        Results include posts from any subreddit matching the query string,
        providing broader coverage than subreddit-specific fetching.
        """
        posts: list[RawPostData] = []
        async for submission in reddit.search(
            query,
            sort=self.SEARCH_SORT,
            limit=self.SEARCH_FETCH_LIMIT,
        ):
            created_at = datetime.fromtimestamp(submission.created_utc, tz=UTC)
            if since and created_at < since:
                continue
            content = self._build_content(submission)
            posts.append(
                {
                    "external_id": f"reddit_{submission.id}",
                    "raw_content": content,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "author": str(submission.author) if submission.author else None,
                    "posted_at": created_at.isoformat(),
                    "metadata": {
                        "subreddit": str(submission.subreddit)
                        if hasattr(submission, "subreddit")
                        else None,
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "flair": submission.link_flair_text
                        if hasattr(submission, "link_flair_text")
                        and submission.link_flair_text
                        else None,
                        "title": submission.title,
                    },
                }
            )
        return posts

    def _build_content(self, submission) -> str:
        # Combines all useful text fields into a single string for keyword filtering + LLM extraction.
        # The double-newline separator helps the LLM parse distinct sections.
        parts = [f"Title: {submission.title}"]
        # Self-text body (present for text posts, empty for link-only posts)
        if hasattr(submission, "selftext") and submission.selftext:
            parts.append(f"Body: {submission.selftext}")
        # Flair tag (e.g., [Hiring], [For Hire]) — strong job signal
        if hasattr(submission, "link_flair_text") and submission.link_flair_text:
            parts.append(f"Flair: {submission.link_flair_text}")
        # External URL (present for link posts — may point to the actual job listing)
        if hasattr(submission, "url") and submission.url:
            parts.append(f"URL: {submission.url}")
        return "\n\n".join(parts)
