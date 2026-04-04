from fastapi import APIRouter, Header, HTTPException

from core.config import settings
from core.database import get_pool
from models.schemas import ScanRunResponse, TriggerScanResponse
from pipeline.graph import run_pipeline

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("/trigger", response_model=TriggerScanResponse)
async def trigger_scan(
    source: str = "reddit",
    x_cron_secret: str | None = Header(None),
):
    if settings.CRON_SECRET:
        if x_cron_secret != settings.CRON_SECRET:
            raise HTTPException(status_code=401, detail="Invalid cron secret")

    pool = await get_pool()

    source_row = await pool.fetchrow(
        "SELECT id FROM sources WHERE name = $1 AND is_active = true", source
    )
    if not source_row:
        raise HTTPException(
            status_code=404, detail=f"Source '{source}' not found or inactive"
        )

    scan_row = await pool.fetchrow(
        """INSERT INTO scan_runs (source_name, status) VALUES ($1, 'running') RETURNING id""",
        source,
    )
    scan_run_id = scan_row["id"]

    try:
        await run_pipeline(source, scan_run_id)
    except Exception as e:
        await pool.execute(
            "UPDATE scan_runs SET status = 'failed', errors = 1, finished_at = NOW() WHERE id = $1",
            scan_run_id,
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
        "SELECT * FROM scan_runs ORDER BY started_at DESC LIMIT $1", limit
    )
    return [
        ScanRunResponse(
            id=row["id"],
            sourceName=row["source_name"],
            status=row["status"],
            postsFound=row["posts_found"],
            postsNew=row["posts_new"],
            jobsAdded=row["jobs_added"],
            errors=row["errors"],
            startedAt=row["started_at"],
            finishedAt=row["finished_at"],
        )
        for row in rows
    ]
