from fastapi import APIRouter, HTTPException, Query

from core.database import get_pool
from models.schemas import CreateSavedSearch, SavedSearchResponse

router = APIRouter(prefix="/searches", tags=["searches"])


@router.get("", response_model=list[SavedSearchResponse])
async def list_searches(userId: str = Query(...)):
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM saved_searches WHERE user_id = $1 ORDER BY created_at DESC",
        userId,
    )
    return [
        SavedSearchResponse(
            id=row["id"],
            keywords=row["keywords"],
            location=row["location"],
            jobType=row["job_type"],
            isActive=row["is_active"],
            createdAt=row["created_at"],
        )
        for row in rows
    ]


@router.post("", response_model=SavedSearchResponse, status_code=201)
async def create_search(data: CreateSavedSearch, userId: str = Query(...)):
    pool = await get_pool()
    row = await pool.fetchrow(
        """INSERT INTO saved_searches (user_id, keywords, location, job_type)
        VALUES ($1, $2, $3, $4) RETURNING *""",
        userId,
        data.keywords,
        data.location,
        data.jobType,
    )
    return SavedSearchResponse(
        id=row["id"],
        keywords=row["keywords"],
        location=row["location"],
        jobType=row["job_type"],
        isActive=row["is_active"],
        createdAt=row["created_at"],
    )


@router.delete("/{search_id}", status_code=204)
async def delete_search(search_id: str, userId: str = Query(...)):
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM saved_searches WHERE id = $1 AND user_id = $2",
        search_id,
        userId,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Search not found")
