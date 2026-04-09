from pipeline.source_configs import get_source_config
from pipeline.sources.registry import get_source
from pipeline.state import PipelineState

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
    source_name = state["source_name"]
    config = get_source_config(source_name)
    source = get_source(source_name, **config)

    if source and source.skip_keyword_filter():
        return {"filtered_posts": state["raw_posts"]}

    filtered = []
    for post in state["raw_posts"]:
        content_lower = post["raw_content"].lower()
        if any(kw in content_lower for kw in JOB_KEYWORDS):
            filtered.append(post)
    return {"filtered_posts": filtered}
