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
    sourceName: str | None = None
    metadata: dict | None = None
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


class CreateAgent(BaseModel):
    name: str
    jobTitle: str
    skills: list[str] = []
    location: str | None = None
    openToRelocate: bool = False
    experienceLevel: str | None = None
    salaryMin: int | None = None
    salaryMax: int | None = None
    jobType: str | None = None
    sources: list[str] = ["reddit"]
    scanIntervalMinutes: int = 1440


class UpdateAgent(BaseModel):
    name: str | None = None
    jobTitle: str | None = None
    skills: list[str] | None = None
    location: str | None = None
    openToRelocate: bool | None = None
    experienceLevel: str | None = None
    salaryMin: int | None = None
    salaryMax: int | None = None
    jobType: str | None = None
    sources: list[str] | None = None
    scanIntervalMinutes: int | None = None
    isActive: bool | None = None


class AgentResponse(BaseModel):
    id: str
    userId: str
    name: str
    jobTitle: str
    skills: list[str]
    location: str | None = None
    openToRelocate: bool
    experienceLevel: str | None = None
    salaryMin: int | None = None
    salaryMax: int | None = None
    jobType: str | None = None
    sources: list[str]
    scanIntervalMinutes: int
    isActive: bool
    lastRunAt: datetime | None = None
    nextRunAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime
    totalResults: int = 0
    unviewedResults: int = 0
    latestRunStatus: str | None = None


class AgentRunResponse(BaseModel):
    id: str
    agentId: str
    status: str
    postsScanned: int
    jobsFound: int
    newJobs: int
    startedAt: datetime
    finishedAt: datetime | None = None
    error: str | None = None


class AgentResultResponse(BaseModel):
    id: str
    agentId: str
    listingId: str
    relevanceScore: float
    matchReason: str | None = None
    isViewed: bool
    createdAt: datetime
    listing: ListingResponse
