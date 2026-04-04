import pytest
from pipeline.state import PipelineState


@pytest.mark.asyncio
async def test_pipeline_state_structure():
    state: PipelineState = {
        "source_name": "reddit",
        "scan_run_id": "test",
        "subreddits": ["forhire"],
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
    assert state["source_name"] == "reddit"
    assert state["subreddits"] == ["forhire"]
    assert state["errors"] == 0
