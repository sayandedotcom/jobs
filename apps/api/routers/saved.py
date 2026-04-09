from fastapi import APIRouter, HTTPException, Query

from core.database import get_pool
from core.utils import cuid
from models.schemas import (
    CreateSavedJob,
    ListingResponse,
    UpdateSavedJob,
    UserSavedJobResponse,
)

router = APIRouter(prefix="/saved", tags=["saved"])


@router.get("", response_model=list[UserSavedJobResponse])
async def list_saved_jobs(userId: str = Query(...)):
    pool = await get_pool()
    rows = await pool.fetch(
        """SELECT usj.*, l.id as l_id, l.title as l_title, l.company as l_company,
        l.description as l_description, l.location as l_location, l.salary as l_salary,
        l.url as l_url, l."jobType" as l_job_type, l."applyUrl" as l_apply_url,
        l."postedAt" as l_posted_at, l."createdAt" as l_created_at,
        l."sourceName" as l_source_name, l.metadata as l_metadata
        FROM user_saved_jobs usj
        JOIN listings l ON l.id = usj."listingId"
        WHERE usj."userId" = $1
        ORDER BY usj."createdAt" DESC""",
        userId,
    )
    result = []
    for row in rows:
        result.append(
            UserSavedJobResponse(
                id=row["id"],
                listingId=row["listingId"],
                status=row["status"],
                notes=row["notes"],
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
                createdAt=row["createdAt"],
            )
        )
    return result


@router.post("", response_model=UserSavedJobResponse, status_code=201)
async def save_job(data: CreateSavedJob, userId: str = Query(...)):
    pool = await get_pool()
    existing = await pool.fetchrow(
        """SELECT id FROM user_saved_jobs WHERE "userId" = $1 AND "listingId" = $2""",
        userId,
        data.listingId,
    )
    if existing:
        raise HTTPException(status_code=409, detail="Job already saved")

    listing = await pool.fetchrow(
        "SELECT * FROM listings WHERE id = $1", data.listingId
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    row = await pool.fetchrow(
        """INSERT INTO user_saved_jobs (id, "userId", "listingId", status)
        VALUES ($1, $2, $3, 'saved') RETURNING *""",
        cuid(),
        userId,
        data.listingId,
    )
    return UserSavedJobResponse(
        id=row["id"],
        listingId=row["listingId"],
        status=row["status"],
        notes=row["notes"],
        listing=ListingResponse(
            id=listing["id"],
            title=listing["title"],
            company=listing["company"],
            description=listing["description"],
            location=listing["location"],
            salary=listing["salary"],
            url=listing["url"],
            jobType=listing["jobType"],
            applyUrl=listing["applyUrl"],
            postedAt=listing["postedAt"],
            createdAt=listing["createdAt"],
            sourceName=listing["sourceName"],
            metadata=listing["metadata"],
        ),
        createdAt=row["createdAt"],
    )


@router.patch("/{saved_id}", response_model=UserSavedJobResponse)
async def update_saved_job(
    saved_id: str, data: UpdateSavedJob, userId: str = Query(...)
):
    pool = await get_pool()
    existing = await pool.fetchrow(
        """SELECT * FROM user_saved_jobs WHERE id = $1 AND "userId" = $2""",
        saved_id,
        userId,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Saved job not found")

    updates = []
    params = []
    idx = 1
    if data.status is not None:
        updates.append(f"status = ${idx}")
        params.append(data.status)
        idx += 1
    if data.notes is not None:
        updates.append(f"notes = ${idx}")
        params.append(data.notes)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.extend([saved_id, userId])
    row = await pool.fetchrow(
        f"""UPDATE user_saved_jobs SET {", ".join(updates)} WHERE id = ${idx} AND "userId" = ${idx + 1}
        RETURNING *""",
        *params,
    )

    listing = await pool.fetchrow(
        """SELECT * FROM listings WHERE id = $1""", row["listingId"]
    )

    return UserSavedJobResponse(
        id=row["id"],
        listingId=row["listingId"],
        status=row["status"],
        notes=row["notes"],
        listing=ListingResponse(
            id=listing["id"],
            title=listing["title"],
            company=listing["company"],
            description=listing["description"],
            location=listing["location"],
            salary=listing["salary"],
            url=listing["url"],
            jobType=listing["jobType"],
            applyUrl=listing["applyUrl"],
            postedAt=listing["postedAt"],
            createdAt=listing["createdAt"],
            sourceName=listing["sourceName"],
            metadata=listing["metadata"],
        ),
        createdAt=row["createdAt"],
    )


@router.delete("/by-listing/{listing_id}", status_code=204)
async def delete_saved_job_by_listing(listing_id: str, userId: str = Query(...)):
    pool = await get_pool()
    result = await pool.execute(
        """DELETE FROM user_saved_jobs WHERE "listingId" = $1 AND "userId" = $2""",
        listing_id,
        userId,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Saved job not found")


@router.delete("/{saved_id}", status_code=204)
async def delete_saved_job(saved_id: str, userId: str = Query(...)):
    pool = await get_pool()
    result = await pool.execute(
        """DELETE FROM user_saved_jobs WHERE id = $1 AND "userId" = $2""",
        saved_id,
        userId,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Saved job not found")
