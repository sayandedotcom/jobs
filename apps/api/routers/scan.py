from datetime import datetime, UTC

from fastapi import APIRouter, Header, HTTPException

from core.config import settings
from core.database import get_pool
from core.utils import cuid
from models.schemas import ScanRunResponse, TriggerScanResponse
from pipeline.graph import run_pipeline

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("/trigger", response_model=TriggerScanResponse)
async def trigger_scan(
    source: str,
    x_cron_secret: str | None = Header(None),
):
    if settings.CRON_SECRET:
        if x_cron_secret != settings.CRON_SECRET:
            raise HTTPException(status_code=401, detail="Invalid cron secret")

    pool = await get_pool()

    source_row = await pool.fetchrow("SELECT id FROM sources WHERE name = $1", source)
    if not source_row:
        raise HTTPException(status_code=404, detail=f"Source '{source}' not found")

    scan_id = cuid()
    scan_row = await pool.fetchrow(
        """INSERT INTO scan_runs (id, "sourceName", status) VALUES ($1, $2, 'running') RETURNING id""",
        scan_id,
        source,
    )
    scan_run_id = scan_row["id"]

    try:
        await run_pipeline(source, scan_run_id)
    except Exception as e:
        await pool.execute(
            """UPDATE scan_runs SET status = 'failed', errors = 1, "finishedAt" = $2 WHERE id = $1""",
            scan_run_id,
            datetime.now(UTC).replace(tzinfo=None),
        )
        raise HTTPException(status_code=500, detail=str(e))

    return TriggerScanResponse(
        message="Scan completed",
        scanRunId=scan_run_id,
    )


@router.get("/runs", response_model=list[ScanRunResponse])
async def list_scan_runs(limit: int = 20):
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT * FROM scan_runs ORDER BY "startedAt" DESC LIMIT $1""",
        limit,
    )
    return [
        ScanRunResponse(
            id=row["id"],
            sourceName=row["sourceName"],
            status=row["status"],
            postsFound=row["postsFound"],
            postsNew=row["postsNew"],
            jobsAdded=row["jobsAdded"],
            errors=row["errors"],
            startedAt=row["startedAt"],
            finishedAt=row["finishedAt"],
        )
        for row in rows
    ]
