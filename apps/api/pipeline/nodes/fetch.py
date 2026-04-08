from core.database import get_pool
from pipeline.source_configs import get_source_config
from pipeline.sources.registry import get_source
from pipeline.state import PipelineState


async def fetch_node(state: PipelineState) -> dict:
    pool = await get_pool()
    source_name = state["source_name"]

    config = get_source_config(source_name)
    source = get_source(source_name, **config)
    if not source:
        return {"raw_posts": [], "errors": state["errors"] + 1}

    rows = await pool.fetch(
        """SELECT name, type FROM sub_sources WHERE "sourceId" = (SELECT id FROM sources WHERE name = $1)""",
        source_name,
    )
    sub_sources = [{"name": row["name"], "type": row["type"]} for row in rows]
    if not sub_sources:
        return {"raw_posts": [], "sub_sources": []}

    last_scan = await pool.fetchrow(
        """SELECT "startedAt" FROM scan_runs WHERE "sourceName" = $1 AND status = 'completed' ORDER BY "startedAt" DESC LIMIT 1""",
        source_name,
    )
    since = last_scan["startedAt"] if last_scan else None
    if since and hasattr(since, "replace") and since.tzinfo is not None:
        since = since.replace(tzinfo=None)

    try:
        raw_posts = await source.fetch_new_posts(sub_sources, since)
    except Exception:
        return {"raw_posts": [], "errors": state["errors"] + 1}

    return {
        "raw_posts": raw_posts,
        "posts_found": len(raw_posts),
        "sub_sources": sub_sources,
    }
