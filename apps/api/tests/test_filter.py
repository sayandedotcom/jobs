import pytest
from pipeline.nodes.filter import JOB_KEYWORDS, filter_node
from pipeline.state import PipelineState, RawPostData


def _make_post(content: str) -> RawPostData:
    return {
        "external_id": "test_1",
        "raw_content": content,
        "permalink": None,
        "author": None,
        "posted_at": None,
    }


@pytest.mark.asyncio
async def test_filter_node_keeps_job_posts():
    state: PipelineState = {
        "source_name": "reddit",
        "scan_run_id": "test",
        "subreddits": [],
        "raw_posts": [
            _make_post("[Hiring] Senior React Developer at Google"),
            _make_post("Looking for a remote Python engineer"),
            _make_post("What's your favorite code editor?"),
            _make_post("Full-time position available for DevOps"),
        ],
        "filtered_posts": [],
        "extracted_jobs": [],
        "new_listings": [],
        "matched_listings": [],
        "posts_found": 4,
        "posts_new": 0,
        "jobs_added": 0,
        "errors": 0,
    }
    result = await filter_node(state)
    assert len(result["filtered_posts"]) == 3
    assert "What's your favorite code editor?" not in [
        p["raw_content"] for p in result["filtered_posts"]
    ]


@pytest.mark.asyncio
async def test_filter_node_empty_input():
    state: PipelineState = {
        "source_name": "reddit",
        "scan_run_id": "test",
        "subreddits": [],
        "raw_posts": [],
        "filtered_posts": [],
        "extracted_jobs": [],
        "new_listings": [],
        "matched_listings": [],
        "posts_found": 0,
        "posts_new": 0,
        "jobs_added": 0,
        "errors": 0,
    }
    result = await filter_node(state)
    assert len(result["filtered_posts"]) == 0


def test_job_keywords_exist():
    assert len(JOB_KEYWORDS) > 10
    assert "hiring" in JOB_KEYWORDS
    assert "remote" in JOB_KEYWORDS
