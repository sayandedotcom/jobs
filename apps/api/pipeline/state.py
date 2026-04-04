from typing import TypedDict


class RawPostData(TypedDict):
    external_id: str
    raw_content: str
    permalink: str | None
    author: str | None
    posted_at: str | None


class ExtractedJob(TypedDict):
    title: str
    company: str
    description: str
    location: str | None
    salary: str | None
    job_type: str | None
    apply_url: str | None
    is_job_posting: bool


class PipelineState(TypedDict):
    source_name: str
    scan_run_id: str
    subreddits: list[str]
    raw_posts: list[RawPostData]
    filtered_posts: list[RawPostData]
    extracted_jobs: list[tuple[RawPostData, ExtractedJob]]
    new_listings: list[dict]
    matched_listings: list[tuple[str, str]]
    posts_found: int
    posts_new: int
    jobs_added: int
    errors: int
