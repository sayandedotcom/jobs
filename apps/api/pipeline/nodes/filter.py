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
    filtered = []
    for post in state["raw_posts"]:
        content_lower = post["raw_content"].lower()
        if any(kw in content_lower for kw in JOB_KEYWORDS):
            filtered.append(post)
    return {"filtered_posts": filtered}
