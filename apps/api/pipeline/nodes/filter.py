from pipeline.state import PipelineState

# Generic job-related keywords for quick pre-filtering before LLM extraction.
# This reduces the number of expensive LLM calls by discarding clearly unrelated posts.
# Applied as simple substring matching against the lowercased raw_content.
JOB_KEYWORDS = [
    "hiring",
    "job",
    "position",
    "opening",
    "looking for",
    "seeking",
    "recruiting",
    "remote",
    "full-time",
    "part-time",
    "contract",
    "freelance",
    "opportunity",
    "career",
    "vacancy",
    "role",
    "engineer",
    "developer",
    "designer",
    "manager",
    "analyst",
    "intern",
    "senior",
    "junior",
    "lead",
    "staff",
    "frontend",
    "backend",
    "fullstack",
    "devops",
    "[hiring]",
    "[for hire]",
]


async def filter_node(state: PipelineState) -> dict:
    """LangGraph node: cheap keyword-based filter to discard non-job posts.

    Keeps any post whose raw_content contains at least one JOB_KEYWORD substring.
    This is intentionally over-inclusive (high recall) — the LLM extract step
    handles precision by classifying is_job_posting.
    """
    filtered = []
    for post in state["raw_posts"]:
        content_lower = post["raw_content"].lower()
        if any(kw in content_lower for kw in JOB_KEYWORDS):
            filtered.append(post)
    return {"filtered_posts": filtered}
