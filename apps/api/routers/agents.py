import json
from datetime import datetime, UTC, timedelta

from fastapi import APIRouter, HTTPException, Query

from core.database import get_pool
from models.schemas import (
    AgentResponse,
    AgentResultResponse,
    AgentRunResponse,
    CreateAgent,
    ListingResponse,
    UpdateAgent,
)

router = APIRouter(prefix="/agents", tags=["agents"])

MIN_SCAN_INTERVAL = 30

PLAN_AGENT_LIMITS: dict[str, int] = {
    "free": 0,
    "pro": 5,
    "enterprise": -1,
}


def _agent_row_to_response(
    row, total_results: int = 0, unviewed: int = 0, latest_status: str | None = None
) -> AgentResponse:
    skills = (
        row["skills"]
        if isinstance(row["skills"], list)
        else json.loads(row["skills"] or "[]")
    )
    sources = (
        row["sources"]
        if isinstance(row["sources"], list)
        else json.loads(row["sources"] or "[]")
    )
    return AgentResponse(
        id=row["id"],
        userId=row["user_id"],
        name=row["name"],
        jobTitle=row["job_title"],
        skills=skills,
        location=row["location"],
        openToRelocate=row["open_to_relocate"],
        experienceLevel=row["experience_level"],
        salaryMin=row["salary_min"],
        salaryMax=row["salary_max"],
        jobType=row["job_type"],
        sources=sources,
        scanIntervalMinutes=row["scan_interval_minutes"],
        isActive=row["is_active"],
        lastRunAt=row["last_run_at"],
        nextRunAt=row["next_run_at"],
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
        totalResults=total_results,
        unviewedResults=unviewed,
        latestRunStatus=latest_status,
    )


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(data: CreateAgent, userId: str = Query(...)):
    if data.scanIntervalMinutes < MIN_SCAN_INTERVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Scan interval must be at least {MIN_SCAN_INTERVAL} minutes",
        )

    pool = await get_pool()

    user = await pool.fetchrow("SELECT plan FROM user WHERE id = $1", userId)
    user_plan = user["plan"] if user else "free"
    limit = PLAN_AGENT_LIMITS.get(user_plan, 0)

    if limit == 0:
        raise HTTPException(
            status_code=403,
            detail="Free plan does not include agent creation. Please upgrade to Pro.",
        )

    if limit > 0:
        active_count = await pool.fetchval(
            "SELECT COUNT(*) FROM agents WHERE user_id = $1 AND is_active = true",
            userId,
        )
        if active_count >= limit:
            raise HTTPException(
                status_code=403,
                detail=f"Agent limit reached ({limit} for {user_plan} plan). Please upgrade or deactivate existing agents.",
            )
    next_run = datetime.now(UTC) + timedelta(minutes=data.scanIntervalMinutes)
    row = await pool.fetchrow(
        """INSERT INTO agents (user_id, name, job_title, skills, location, open_to_relocate,
           experience_level, salary_min, salary_max, job_type, sources, scan_interval_minutes, next_run_at)
        VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, $13)
        RETURNING *""",
        userId,
        data.name,
        data.jobTitle,
        json.dumps(data.skills),
        data.location,
        data.openToRelocate,
        data.experienceLevel,
        data.salaryMin,
        data.salaryMax,
        data.jobType,
        json.dumps(data.sources),
        data.scanIntervalMinutes,
        next_run,
    )
    return _agent_row_to_response(row)


@router.get("", response_model=list[AgentResponse])
async def list_agents(userId: str = Query(...)):
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM agents WHERE user_id = $1 ORDER BY created_at DESC",
        userId,
    )
    result = []
    for row in rows:
        total = await pool.fetchval(
            "SELECT COUNT(*) FROM agent_results WHERE agent_id = $1",
            row["id"],
        )
        unviewed = await pool.fetchval(
            "SELECT COUNT(*) FROM agent_results WHERE agent_id = $1 AND is_viewed = false",
            row["id"],
        )
        latest_run = await pool.fetchrow(
            "SELECT status FROM agent_runs WHERE agent_id = $1 ORDER BY started_at DESC LIMIT 1",
            row["id"],
        )
        latest_status = latest_run["status"] if latest_run else None
        result.append(_agent_row_to_response(row, total, unviewed, latest_status))
    return result


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, userId: str = Query(...)):
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM agents WHERE id = $1 AND user_id = $2",
        agent_id,
        userId,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    total = await pool.fetchval(
        "SELECT COUNT(*) FROM agent_results WHERE agent_id = $1",
        agent_id,
    )
    unviewed = await pool.fetchval(
        "SELECT COUNT(*) FROM agent_results WHERE agent_id = $1 AND is_viewed = false",
        agent_id,
    )
    latest_run = await pool.fetchrow(
        "SELECT status FROM agent_runs WHERE agent_id = $1 ORDER BY started_at DESC LIMIT 1",
        agent_id,
    )
    latest_status = latest_run["status"] if latest_run else None
    return _agent_row_to_response(row, total, unviewed, latest_status)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, data: UpdateAgent, userId: str = Query(...)):
    pool = await get_pool()
    existing = await pool.fetchrow(
        "SELECT * FROM agents WHERE id = $1 AND user_id = $2",
        agent_id,
        userId,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Agent not found")

    updates = []
    params = []
    idx = 1

    field_map = {
        "name": ("name", None),
        "jobTitle": ("job_title", None),
        "location": ("location", None),
        "openToRelocate": ("open_to_relocate", None),
        "experienceLevel": ("experience_level", None),
        "salaryMin": ("salary_min", None),
        "salaryMax": ("salary_max", None),
        "jobType": ("job_type", None),
        "isActive": ("is_active", None),
    }

    for field, (col, _) in field_map.items():
        val = getattr(data, field, None)
        if val is not None:
            updates.append(f"{col} = ${idx}")
            params.append(val)
            idx += 1

    if data.skills is not None:
        updates.append(f"skills = ${idx}::jsonb")
        params.append(json.dumps(data.skills))
        idx += 1

    if data.sources is not None:
        updates.append(f"sources = ${idx}::jsonb")
        params.append(json.dumps(data.sources))
        idx += 1

    if data.scanIntervalMinutes is not None:
        if data.scanIntervalMinutes < MIN_SCAN_INTERVAL:
            raise HTTPException(
                status_code=400,
                detail=f"Scan interval must be at least {MIN_SCAN_INTERVAL} minutes",
            )
        updates.append(f"scan_interval_minutes = ${idx}")
        params.append(data.scanIntervalMinutes)
        idx += 1
        updates.append(f"next_run_at = ${idx}")
        params.append(datetime.now(UTC) + timedelta(minutes=data.scanIntervalMinutes))
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.extend([agent_id, userId])
    row = await pool.fetchrow(
        f"""UPDATE agents SET {", ".join(updates)} WHERE id = ${idx} AND user_id = ${idx + 1}
        RETURNING *""",
        *params,
    )

    total = await pool.fetchval(
        "SELECT COUNT(*) FROM agent_results WHERE agent_id = $1",
        agent_id,
    )
    unviewed = await pool.fetchval(
        "SELECT COUNT(*) FROM agent_results WHERE agent_id = $1 AND is_viewed = false",
        agent_id,
    )
    latest_run = await pool.fetchrow(
        "SELECT status FROM agent_runs WHERE agent_id = $1 ORDER BY started_at DESC LIMIT 1",
        agent_id,
    )
    latest_status = latest_run["status"] if latest_run else None
    return _agent_row_to_response(row, total, unviewed, latest_status)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, userId: str = Query(...)):
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM agents WHERE id = $1 AND user_id = $2",
        agent_id,
        userId,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Agent not found")


@router.get("/{agent_id}/results", response_model=list[AgentResultResponse])
async def list_agent_results(
    agent_id: str,
    userId: str = Query(...),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
):
    pool = await get_pool()
    agent = await pool.fetchrow(
        "SELECT id FROM agents WHERE id = $1 AND user_id = $2",
        agent_id,
        userId,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    offset = (page - 1) * pageSize
    rows = await pool.fetch(
        """SELECT ar.*, l.id as l_id, l.title as l_title, l.company as l_company,
        l.description as l_description, l.location as l_location, l.salary as l_salary,
        l.url as l_url, l.job_type as l_job_type, l.apply_url as l_apply_url,
        l.posted_at as l_posted_at, l.created_at as l_created_at
        FROM agent_results ar
        JOIN listings l ON l.id = ar.listing_id
        WHERE ar.agent_id = $1
        ORDER BY ar.relevance_score DESC
        LIMIT $2 OFFSET $3""",
        agent_id,
        pageSize,
        offset,
    )
    results = []
    for row in rows:
        results.append(
            AgentResultResponse(
                id=row["id"],
                agentId=row["agent_id"],
                listingId=row["listing_id"],
                relevanceScore=row["relevance_score"],
                matchReason=row["match_reason"],
                isViewed=row["is_viewed"],
                createdAt=row["created_at"],
                listing=ListingResponse(
                    id=row["l_id"],
                    title=row["l_title"],
                    company=row["l_company"],
                    description=row["l_description"],
                    location=row["l_location"],
                    salary=row["l_salary"],
                    url=row["l_url"],
                    jobType=row["l_job_type"],
                    applyUrl=row["l_apply_url"],
                    postedAt=row["l_posted_at"],
                    createdAt=row["l_created_at"],
                ),
            )
        )
    return results


@router.get("/{agent_id}/runs", response_model=list[AgentRunResponse])
async def list_agent_runs(
    agent_id: str,
    userId: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
):
    pool = await get_pool()
    agent = await pool.fetchrow(
        "SELECT id FROM agents WHERE id = $1 AND user_id = $2",
        agent_id,
        userId,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    rows = await pool.fetch(
        "SELECT * FROM agent_runs WHERE agent_id = $1 ORDER BY started_at DESC LIMIT $2",
        agent_id,
        limit,
    )
    return [
        AgentRunResponse(
            id=row["id"],
            agentId=row["agent_id"],
            status=row["status"],
            postsScanned=row["posts_scanned"],
            jobsFound=row["jobs_found"],
            newJobs=row["new_jobs"],
            startedAt=row["started_at"],
            finishedAt=row["finished_at"],
            error=row["error"],
        )
        for row in rows
    ]


@router.post("/{agent_id}/trigger", response_model=AgentRunResponse)
async def trigger_agent(agent_id: str, userId: str = Query(...)):
    pool = await get_pool()
    agent = await pool.fetchrow(
        "SELECT * FROM agents WHERE id = $1 AND user_id = $2",
        agent_id,
        userId,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    from pipeline.agent_graph import run_agent_pipeline

    run_row = await pool.fetchrow(
        """INSERT INTO agent_runs (agent_id, status) VALUES ($1, 'running') RETURNING *""",
        agent_id,
    )

    try:
        await run_agent_pipeline(dict(agent), run_row["id"])
        run_row = await pool.fetchrow(
            "SELECT * FROM agent_runs WHERE id = $1",
            run_row["id"],
        )
    except Exception as e:
        await pool.execute(
            "UPDATE agent_runs SET status = 'failed', error = $1, finished_at = NOW() WHERE id = $2",
            str(e),
            run_row["id"],
        )
        run_row = await pool.fetchrow(
            "SELECT * FROM agent_runs WHERE id = $1",
            run_row["id"],
        )

    return AgentRunResponse(
        id=run_row["id"],
        agentId=run_row["agent_id"],
        status=run_row["status"],
        postsScanned=run_row["posts_scanned"],
        jobsFound=run_row["jobs_found"],
        newJobs=run_row["new_jobs"],
        startedAt=run_row["started_at"],
        finishedAt=run_row["finished_at"],
        error=run_row["error"],
    )


@router.patch("/{agent_id}/results/{result_id}/view", status_code=204)
async def mark_result_viewed(result_id: str, agent_id: str, userId: str = Query(...)):
    pool = await get_pool()
    agent = await pool.fetchrow(
        "SELECT id FROM agents WHERE id = $1 AND user_id = $2",
        agent_id,
        userId,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await pool.execute(
        "UPDATE agent_results SET is_viewed = true WHERE id = $1 AND agent_id = $2",
        result_id,
        agent_id,
    )
