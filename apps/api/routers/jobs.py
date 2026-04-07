from fastapi import APIRouter, Query

from core.database import get_pool
from models.schemas import ListingListResponse, ListingResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=ListingListResponse)
async def list_jobs(
    search: str | None = Query(None),
    location: str | None = Query(None),
    jobType: str | None = Query(None),
    company: str | None = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    userId: str | None = Query(None),
):
    pool = await get_pool()
    offset = (page - 1) * pageSize
    conditions = []
    params = []
    idx = 1

    if search:
        conditions.append(
            f"(l.title ILIKE ${idx} OR l.description ILIKE ${idx} OR l.company ILIKE ${idx})"
        )
        params.append(f"%{search}%")
        idx += 1
    if location:
        conditions.append(f"l.location ILIKE ${idx}")
        params.append(f"%{location}%")
        idx += 1
    if jobType:
        conditions.append(f"l.job_type = ${idx}")
        params.append(jobType)
        idx += 1
    if company:
        conditions.append(f"l.company ILIKE ${idx}")
        params.append(f"%{company}%")
        idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    count_row = await pool.fetchrow(
        f"SELECT COUNT(*) as total FROM listings l {where_clause}", *params
    )
    total = count_row["total"]

    rows = await pool.fetch(
        f"""SELECT l.* {" , usj.id as save_id" if userId else ""}
        FROM listings l
        {"LEFT JOIN user_saved_jobs usj ON usj.listing_id = l.id AND usj.user_id = $" + str(idx) if userId else ""}
        {where_clause}
        ORDER BY l.created_at DESC
        LIMIT ${idx + (1 if userId else 0)} OFFSET ${idx + (1 if userId else 0) + 1}""",
        *params,
        *([userId] if userId else []),
        pageSize,
        offset,
    )

    jobs = []
    for row in rows:
        jobs.append(
            ListingResponse(
                id=row["id"],
                title=row["title"],
                company=row["company"],
                description=row["description"],
                location=row["location"],
                salary=row["salary"],
                url=row["url"],
                jobType=row["job_type"],
                applyUrl=row["apply_url"],
                sourceName=row["source_name"],
                metadata=row["metadata"],
                postedAt=row["posted_at"],
                createdAt=row["created_at"],
                isSaved=row.get("save_id") is not None if userId else False,
            )
        )

    return ListingListResponse(jobs=jobs, total=total, page=page, pageSize=pageSize)


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_job(listing_id: str):
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM listings WHERE id = $1", listing_id)
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Job not found")
    return ListingResponse(
        id=row["id"],
        title=row["title"],
        company=row["company"],
        description=row["description"],
        location=row["location"],
        salary=row["salary"],
        url=row["url"],
        jobType=row["job_type"],
        applyUrl=row["apply_url"],
        sourceName=row["source_name"],
        metadata=row["metadata"],
        postedAt=row["posted_at"],
        createdAt=row["created_at"],
    )
