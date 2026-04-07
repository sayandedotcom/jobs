from typing import TypedDict


class RawPostData(TypedDict):
    """Raw post fetched from an external source before any processing.

    Fields:
        external_id: Source-prefixed unique ID (e.g., 'reddit_abc123', 'hn_12345')
        raw_content: Combined text content built by the source (title, body, metadata)
        permalink:   Direct URL to the original post on the source platform
        author:      Username or display name of the post author
        posted_at:   ISO 8601 timestamp of when the post was created
        metadata:    Source-specific fields (subreddit, score, points, etc.)
    """

    external_id: str
    raw_content: str
    permalink: str | None
    author: str | None
    posted_at: str | None
    metadata: dict


class PipelineState(TypedDict):
    """LangGraph StateGraph state flowing through: fetch → filter → dedup → store.

    Fields:
        source_name:      The source to scan (must match a registered source name)
        scan_run_id:      DB row ID for tracking this scan run
        sub_sources:      Source-specific channels with type
                          (e.g., [{'name': 'forhire', 'type': 'subreddit'}])
        raw_posts:        Posts returned by the source fetch
        filtered_posts:   Posts that passed keyword filtering
        new_listings:     Deduped posts ready to insert (dict with post, embedding_text)
        matched_listings: (external_id, existing_listing_id) pairs for cross-posts
        posts_found:      Total raw posts fetched
        posts_new:        Posts not seen before (passed exact dedup)
        jobs_added:       New listings actually inserted into the DB
        errors:           Count of failures across all nodes
    """

    source_name: str
    scan_run_id: str
    sub_sources: list[dict]
    raw_posts: list[RawPostData]
    filtered_posts: list[RawPostData]
    new_listings: list[dict]
    matched_listings: list[tuple[str, str]]
    posts_found: int
    posts_new: int
    jobs_added: int
    errors: int
