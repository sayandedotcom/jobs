from datetime import datetime, UTC

import asyncpraw
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


@register_source
class RedditSource(BaseSource):
    """Fetches job postings from Reddit via the asyncpraw client.

    Service details:
        - Uses the Reddit API (OAuth2) through asyncpraw
        - Requires a registered Reddit app: https://www.reddit.com/prefs/apps
        - API credentials: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
        - Rate limits: Reddit allows ~60 requests/min for OAuth2 apps
        - Fetches up to 100 newest posts per subreddit (Reddit API 'new' endpoint)
        - sub_sources for Reddit = subreddit names (e.g., 'forhire', 'remotejs')

    Scalability notes:
        - Each subreddit fetch is a separate API call (sequential inside this class)
        - For many subreddits, consider parallelizing with asyncio.gather()
        - Reddit API pagination limit is 100 items per request
        - No retry/backoff logic currently — wrapped in try/finally only for cleanup
    """

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
        self, sub_sources: list[str], since: datetime | None = None
    ) -> list[RawPostData]:
        # Initialize the asyncpraw Reddit client (unauthenticated "script" mode)
        reddit = asyncpraw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )
        posts: list[RawPostData] = []
        try:
            # Iterate through each subreddit configured in the 'sub_sources' DB table
            for subreddit_name in sub_sources:
                subreddit = await reddit.subreddit(subreddit_name)
                # Fetch up to 100 newest submissions (Reddit API pagination limit)
                async for submission in subreddit.new(limit=100):
                    created_at = datetime.fromtimestamp(submission.created_utc, tz=UTC)
                    # Skip posts older than the last successful scan (incremental fetch)
                    if since and created_at < since:
                        continue
                    # Build a normalized content string from the submission fields
                    content = self._build_content(submission)
                    # Prefix external_id with 'reddit_' to namespace across sources
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
            # Always close the Reddit client to release the HTTP session
            await reddit.close()
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
