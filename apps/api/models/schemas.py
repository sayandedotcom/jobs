from datetime import datetime

from pydantic import BaseModel


class ListingResponse(BaseModel):
    id: str
    title: str
    company: str
    description: str
    location: str | None = None
    salary: str | None = None
    url: str | None = None
    jobType: str | None = None
    applyUrl: str | None = None
    postedAt: datetime | None = None
    createdAt: datetime
    isSaved: bool = False


class ListingListResponse(BaseModel):
    jobs: list[ListingResponse]
    total: int
    page: int
    pageSize: int


class ListingFilters(BaseModel):
    search: str | None = None
    location: str | None = None
    jobType: str | None = None
    company: str | None = None
    page: int = 1
    pageSize: int = 20


class UserSavedJobResponse(BaseModel):
    id: str
    listingId: str
    status: str
    notes: str | None = None
    listing: ListingResponse
    createdAt: datetime


class CreateSavedJob(BaseModel):
    listingId: str


class UpdateSavedJob(BaseModel):
    status: str | None = None
    notes: str | None = None


class SavedSearchResponse(BaseModel):
    id: str
    keywords: str | None = None
    location: str | None = None
    jobType: str | None = None
    isActive: bool
    createdAt: datetime


class CreateSavedSearch(BaseModel):
    keywords: str | None = None
    location: str | None = None
    jobType: str | None = None


class ScanRunResponse(BaseModel):
    id: str
    sourceName: str
    status: str
    postsFound: int
    postsNew: int
    jobsAdded: int
    errors: int
    startedAt: datetime
    finishedAt: datetime | None = None


class TriggerScanResponse(BaseModel):
    message: str
    scanRunId: str
