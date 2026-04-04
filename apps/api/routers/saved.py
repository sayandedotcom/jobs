from fastapi import APIRouter, HTTPException, Query

from core.database import get_pool
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
        l.url as l_url, l.job_type as l_job_type, l.apply_url as l_apply_url,
        l.posted_at as l_posted_at, l.created_at as l_created_at
        FROM user_saved_jobs usj
        JOIN listings l ON l.id = usj.listing_id
        WHERE usj.user_id = $1
        ORDER BY usj.created_at DESC""",
        userId,
    )
    result = []
    for row in rows:
        result.append(
            UserSavedJobResponse(
                id=row["id"],
                listingId=row["listing_id"],
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
                ),
                createdAt=row["created_at"],
            )
        )
    return result


@router.post("", response_model=UserSavedJobResponse, status_code=201)
async def save_job(data: CreateSavedJob, userId: str = Query(...)):
    pool = await get_pool()
    existing = await pool.fetchrow(
        "SELECT id FROM user_saved_jobs WHERE user_id = $1 AND listing_id = $2",
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
        """INSERT INTO user_saved_jobs (user_id, listing_id, status)
        VALUES ($1, $2, 'saved') RETURNING *""",
        userId,
        data.listingId,
    )
    return UserSavedJobResponse(
        id=row["id"],
        listingId=row["listing_id"],
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
            jobType=listing["job_type"],
            applyUrl=listing["apply_url"],
            postedAt=listing["posted_at"],
            createdAt=listing["created_at"],
        ),
        createdAt=row["created_at"],
    )


@router.patch("/{saved_id}", response_model=UserSavedJobResponse)
async def update_saved_job(
    saved_id: str, data: UpdateSavedJob, userId: str = Query(...)
):
    pool = await get_pool()
    existing = await pool.fetchrow(
        "SELECT * FROM user_saved_jobs WHERE id = $1 AND user_id = $2",
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
        f"""UPDATE user_saved_jobs SET {", ".join(updates)} WHERE id = ${idx} AND user_id = ${idx + 1}
        RETURNING *""",
        *params,
    )

    listing = await pool.fetchrow(
        "SELECT * FROM listings WHERE id = $1", row["listing_id"]
    )

    return UserSavedJobResponse(
        id=row["id"],
        listingId=row["listing_id"],
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
            jobType=listing["job_type"],
            applyUrl=listing["apply_url"],
            postedAt=listing["posted_at"],
            createdAt=listing["created_at"],
        ),
        createdAt=row["created_at"],
    )


@router.delete("/{saved_id}", status_code=204)
async def delete_saved_job(saved_id: str, userId: str = Query(...)):
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM user_saved_jobs WHERE id = $1 AND user_id = $2",
        saved_id,
        userId,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Saved job not found")
