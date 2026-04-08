from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException

from core.config import settings
from core.database import get_pool
from core.utils import cuid

router = APIRouter(prefix="/cron", tags=["cron"])


@router.post("/agents", status_code=200)
async def run_due_agents(x_cron_secret: str | None = Header(None)):
    if settings.CRON_SECRET:
        if x_cron_secret != settings.CRON_SECRET:
            raise HTTPException(status_code=401, detail="Invalid cron secret")

    pool = await get_pool()
    now = datetime.now(UTC)
    agents = await pool.fetch(
        """SELECT * FROM agents WHERE "isActive" = true AND "nextRunAt" <= $1""",
        now,
    )

    from pipeline.agent_graph import run_agent_pipeline

    results = []
    for agent in agents:
        run_id = cuid()
        run_row = await pool.fetchrow(
            """INSERT INTO agent_runs (id, "agentId", status) VALUES ($1, $2, 'running') RETURNING *""",
            run_id,
            agent["id"],
        )
        try:
            await run_agent_pipeline(dict(agent), run_row["id"])
            results.append({"agentId": agent["id"], "status": "completed"})
        except Exception as e:
            await pool.execute(
                """UPDATE agent_runs SET status = 'failed', error = $1, "finishedAt" = NOW() WHERE id = $2""",
                str(e),
                run_row["id"],
            )
            results.append(
                {"agentId": agent["id"], "status": "failed", "error": str(e)}
            )

    return {"triggered": len(results), "results": results}
