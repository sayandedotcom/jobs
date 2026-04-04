from core.database import get_pool
from pipeline.state import PipelineState


async def fetch_node(state: PipelineState) -> dict:
    from pipeline.sources.reddit import RedditSource
    from core.config import settings

    pool = await get_pool()
    source_name = state["source_name"]

    if source_name == "reddit":
        source = RedditSource(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )
    else:
        return {"raw_posts": [], "errors": state["errors"] + 1}

    rows = await pool.fetch(
        "SELECT name FROM sub_sources WHERE source_id = (SELECT id FROM sources WHERE name = $1) AND is_active = true",
        source_name,
    )
    subreddits = [row["name"] for row in rows]
    if not subreddits:
        return {"raw_posts": [], "subreddits": []}

    last_scan = await pool.fetchrow(
        "SELECT started_at FROM scan_runs WHERE source_name = $1 AND status = 'completed' ORDER BY started_at DESC LIMIT 1",
        source_name,
    )
    since = last_scan["started_at"] if last_scan else None

    try:
        raw_posts = await source.fetch_new_posts(subreddits, since)
    except Exception:
        return {"raw_posts": [], "errors": state["errors"] + 1}

    return {
        "raw_posts": raw_posts,
        "posts_found": len(raw_posts),
        "subreddits": subreddits,
    }
