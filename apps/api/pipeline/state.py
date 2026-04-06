from typing import TypedDict


class RawPostData(TypedDict):
    """Raw post fetched from an external source before any processing.

    Fields:
        external_id: Source-prefixed unique ID (e.g., 'reddit_abc123', 'linkedin_post_456')
        raw_content: Combined text content built by the source (title, body, metadata)
        permalink:   Direct URL to the original post on the source platform
        author:      Username or display name of the post author
        posted_at:   ISO 8601 timestamp of when the post was created
    """

    external_id: str
    raw_content: str
    permalink: str | None
    author: str | None
    posted_at: str | None


class ExtractedJob(TypedDict):
    """Structured job data extracted from a raw post by the LLM.

    Populated by extract_node / _extract_jobs using Gemini 2.0 Flash.
    Only posts where is_job_posting=true and title is set are kept.
    """

    title: str
    company: str
    description: str
    location: str | None
    salary: str | None
    job_type: str | None
    apply_url: str | None
    is_job_posting: bool


class PipelineState(TypedDict):
    """LangGraph StateGraph state flowing through: fetch → filter → extract → dedup → store.

    Fields:
        source_name:      The source to scan (must match a registered source name)
        scan_run_id:      DB row ID for tracking this scan run
        sub_sources:      Source-specific channels (subreddit names, board slugs, etc.)
        raw_posts:        Posts returned by the source fetch
        filtered_posts:   Posts that passed keyword filtering
        extracted_jobs:   (RawPostData, ExtractedJob) pairs from LLM extraction
        new_listings:     Deduped listings ready to insert (dict with post, job, embedding_text)
        matched_listings: (external_id, existing_listing_id) pairs for cross-posts
        posts_found:      Total raw posts fetched
        posts_new:        Posts not seen before (passed exact dedup)
        jobs_added:       New listings actually inserted into the DB
        errors:           Count of failures across all nodes
    """

    source_name: str
    scan_run_id: str
    sub_sources: list[str]
    raw_posts: list[RawPostData]
    filtered_posts: list[RawPostData]
    extracted_jobs: list[tuple[RawPostData, ExtractedJob]]
    new_listings: list[dict]
    matched_listings: list[tuple[str, str]]
    posts_found: int
    posts_new: int
    jobs_added: int
    errors: int
