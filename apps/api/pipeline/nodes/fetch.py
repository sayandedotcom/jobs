from core.database import get_pool
from pipeline.source_configs import get_source_config
from pipeline.sources.registry import get_source
from pipeline.state import PipelineState


async def fetch_node(state: PipelineState) -> dict:
    """LangGraph node: resolves the source from the registry and fetches raw posts.

    How it works:
        1. Looks up source constructor kwargs from SOURCE_CONFIGS (env vars)
        2. Instantiates the source via the registry factory (get_source)
        3. Queries 'sub_sources' table for active channels (e.g., subreddit names)
        4. Finds the last completed scan run to get an incremental 'since' timestamp
        5. Calls source.fetch_new_posts(sub_sources, since) to get raw data

    This node is source-agnostic — it works with any registered BaseSource.
    The source_name in PipelineState determines which source class is used.
    """
    pool = await get_pool()
    source_name = state["source_name"]

    config = get_source_config(source_name)
    source = get_source(source_name, **config)
    if not source:
        return {"raw_posts": [], "errors": state["errors"] + 1}

    rows = await pool.fetch(
        "SELECT name, type FROM sub_sources WHERE source_id = (SELECT id FROM sources WHERE name = $1) AND is_active = true",
        source_name,
    )
    sub_sources = [{"name": row["name"], "type": row["type"]} for row in rows]
    if not sub_sources:
        return {"raw_posts": [], "sub_sources": []}

    last_scan = await pool.fetchrow(
        "SELECT started_at FROM scan_runs WHERE source_name = $1 AND status = 'completed' ORDER BY started_at DESC LIMIT 1",
        source_name,
    )
    since = last_scan["started_at"] if last_scan else None

    try:
        raw_posts = await source.fetch_new_posts(sub_sources, since)
    except Exception:
        return {"raw_posts": [], "errors": state["errors"] + 1}

    return {
        "raw_posts": raw_posts,
        "posts_found": len(raw_posts),
        "sub_sources": sub_sources,
    }
