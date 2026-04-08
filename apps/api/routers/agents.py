import json
from datetime import datetime, UTC, timedelta

from fastapi import APIRouter, HTTPException, Query

from core.database import get_pool
from core.utils import cuid
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
        userId=row["userId"],
        name=row["name"],
        jobTitle=row["jobTitle"],
        skills=skills,
        location=row["location"],
        openToRelocate=row["openToRelocate"],
        experienceLevel=row["experienceLevel"],
        salaryMin=row["salaryMin"],
        salaryMax=row["salaryMax"],
        jobType=row["jobType"],
        sources=sources,
        scanIntervalMinutes=row["scanIntervalMinutes"],
        isActive=row["isActive"],
        lastRunAt=row["lastRunAt"],
        nextRunAt=row["nextRunAt"],
        createdAt=row["createdAt"],
        updatedAt=row["updatedAt"],
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
            """SELECT COUNT(*) FROM agents WHERE "userId" = $1 AND "isActive" = true""",
            userId,
        )
        if active_count >= limit:
            raise HTTPException(
                status_code=403,
                detail=f"Agent limit reached ({limit} for {user_plan} plan). Please upgrade or deactivate existing agents.",
            )
    next_run = datetime.now(UTC) + timedelta(minutes=data.scanIntervalMinutes)
    agent_id = cuid()
    row = await pool.fetchrow(
        """INSERT INTO agents (id, "userId", name, "jobTitle", skills, location, "openToRelocate",
           "experienceLevel", "salaryMin", "salaryMax", "jobType", sources, "scanIntervalMinutes", "nextRunAt")
        VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, $13, $14)
        RETURNING *""",
        agent_id,
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
        """SELECT * FROM agents WHERE "userId" = $1 ORDER BY "createdAt" DESC""",
        userId,
    )
    result = []
    for row in rows:
        total = await pool.fetchval(
            """SELECT COUNT(*) FROM agent_results WHERE "agentId" = $1""",
            row["id"],
        )
        unviewed = await pool.fetchval(
            """SELECT COUNT(*) FROM agent_results WHERE "agentId" = $1 AND "isViewed" = false""",
            row["id"],
        )
        latest_run = await pool.fetchrow(
            """SELECT status FROM agent_runs WHERE "agentId" = $1 ORDER BY "startedAt" DESC LIMIT 1""",
            row["id"],
        )
        latest_status = latest_run["status"] if latest_run else None
        result.append(_agent_row_to_response(row, total, unviewed, latest_status))
    return result


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, userId: str = Query(...)):
    pool = await get_pool()
    row = await pool.fetchrow(
        """SELECT * FROM agents WHERE id = $1 AND "userId" = $2""",
        agent_id,
        userId,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    total = await pool.fetchval(
        """SELECT COUNT(*) FROM agent_results WHERE "agentId" = $1""",
        agent_id,
    )
    unviewed = await pool.fetchval(
        """SELECT COUNT(*) FROM agent_results WHERE "agentId" = $1 AND "isViewed" = false""",
        agent_id,
    )
    latest_run = await pool.fetchrow(
        """SELECT status FROM agent_runs WHERE "agentId" = $1 ORDER BY "startedAt" DESC LIMIT 1""",
        agent_id,
    )
    latest_status = latest_run["status"] if latest_run else None
    return _agent_row_to_response(row, total, unviewed, latest_status)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, data: UpdateAgent, userId: str = Query(...)):
    pool = await get_pool()
    existing = await pool.fetchrow(
        """SELECT * FROM agents WHERE id = $1 AND "userId" = $2""",
        agent_id,
        userId,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Agent not found")

    updates = []
    params = []
    idx = 1

    field_map = {
        "name": "name",
        "jobTitle": "jobTitle",
        "location": "location",
        "openToRelocate": "openToRelocate",
        "experienceLevel": "experienceLevel",
        "salaryMin": "salaryMin",
        "salaryMax": "salaryMax",
        "jobType": "jobType",
        "isActive": "isActive",
    }

    for field, col in field_map.items():
        val = getattr(data, field, None)
        if val is not None:
            updates.append(f'"{col}" = ${idx}')
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
        updates.append(f'"scanIntervalMinutes" = ${idx}')
        params.append(data.scanIntervalMinutes)
        idx += 1
        updates.append(f'"nextRunAt" = ${idx}')
        params.append(datetime.now(UTC) + timedelta(minutes=data.scanIntervalMinutes))
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.extend([agent_id, userId])
    row = await pool.fetchrow(
        f"""UPDATE agents SET {", ".join(updates)} WHERE id = ${idx} AND "userId" = ${idx + 1}
        RETURNING *""",
        *params,
    )

    total = await pool.fetchval(
        """SELECT COUNT(*) FROM agent_results WHERE "agentId" = $1""",
        agent_id,
    )
    unviewed = await pool.fetchval(
        """SELECT COUNT(*) FROM agent_results WHERE "agentId" = $1 AND "isViewed" = false""",
        agent_id,
    )
    latest_run = await pool.fetchrow(
        """SELECT status FROM agent_runs WHERE "agentId" = $1 ORDER BY "startedAt" DESC LIMIT 1""",
        agent_id,
    )
    latest_status = latest_run["status"] if latest_run else None
    return _agent_row_to_response(row, total, unviewed, latest_status)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, userId: str = Query(...)):
    pool = await get_pool()
    result = await pool.execute(
        """DELETE FROM agents WHERE id = $1 AND "userId" = $2""",
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
        """SELECT id FROM agents WHERE id = $1 AND "userId" = $2""",
        agent_id,
        userId,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    offset = (page - 1) * pageSize
    rows = await pool.fetch(
        """SELECT ar.*, l.id as l_id, l.title as l_title, l.company as l_company,
        l.description as l_description, l.location as l_location, l.salary as l_salary,
        l.url as l_url, l."jobType" as l_job_type, l."applyUrl" as l_apply_url,
        l."postedAt" as l_posted_at, l."createdAt" as l_created_at,
        l."sourceName" as l_source_name, l.metadata as l_metadata
        FROM agent_results ar
        JOIN listings l ON l.id = ar."listingId"
        WHERE ar."agentId" = $1
        ORDER BY ar."relevanceScore" DESC
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
                agentId=row["agentId"],
                listingId=row["listingId"],
                relevanceScore=row["relevanceScore"],
                matchReason=row["matchReason"],
                isViewed=row["isViewed"],
                createdAt=row["createdAt"],
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
                    sourceName=row["l_source_name"],
                    metadata=row["l_metadata"],
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
        """SELECT id FROM agents WHERE id = $1 AND "userId" = $2""",
        agent_id,
        userId,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    rows = await pool.fetch(
        """SELECT * FROM agent_runs WHERE "agentId" = $1 ORDER BY "startedAt" DESC LIMIT $2""",
        agent_id,
        limit,
    )
    return [
        AgentRunResponse(
            id=row["id"],
            agentId=row["agentId"],
            status=row["status"],
            postsScanned=row["postsScanned"],
            jobsFound=row["jobsFound"],
            newJobs=row["newJobs"],
            startedAt=row["startedAt"],
            finishedAt=row["finishedAt"],
            error=row["error"],
        )
        for row in rows
    ]


@router.post("/{agent_id}/trigger", response_model=AgentRunResponse)
async def trigger_agent(agent_id: str, userId: str = Query(...)):
    pool = await get_pool()
    agent = await pool.fetchrow(
        """SELECT * FROM agents WHERE id = $1 AND "userId" = $2""",
        agent_id,
        userId,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    from pipeline.agent_graph import run_agent_pipeline

    run_id = cuid()
    run_row = await pool.fetchrow(
        """INSERT INTO agent_runs (id, "agentId", status) VALUES ($1, $2, 'running') RETURNING *""",
        run_id,
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
            """UPDATE agent_runs SET status = 'failed', error = $1, "finishedAt" = NOW() WHERE id = $2""",
            str(e),
            run_row["id"],
        )
        run_row = await pool.fetchrow(
            "SELECT * FROM agent_runs WHERE id = $1",
            run_row["id"],
        )

    return AgentRunResponse(
        id=run_row["id"],
        agentId=run_row["agentId"],
        status=run_row["status"],
        postsScanned=run_row["postsScanned"],
        jobsFound=run_row["jobsFound"],
        newJobs=run_row["newJobs"],
        startedAt=run_row["startedAt"],
        finishedAt=run_row["finishedAt"],
        error=run_row["error"],
    )


@router.patch("/{agent_id}/results/{result_id}/view", status_code=204)
async def mark_result_viewed(result_id: str, agent_id: str, userId: str = Query(...)):
    pool = await get_pool()
    agent = await pool.fetchrow(
        """SELECT id FROM agents WHERE id = $1 AND "userId" = $2""",
        agent_id,
        userId,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await pool.execute(
        """UPDATE agent_results SET "isViewed" = true WHERE id = $1 AND "agentId" = $2""",
        result_id,
        agent_id,
    )
