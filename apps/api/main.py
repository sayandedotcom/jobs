from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import close_pool
from routers import jobs as jobs_router
from routers import saved as saved_router
from routers import scan as scan_router
from routers import searches as searches_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_pool()


app = FastAPI(title="Jobs API", version="0.1.0", lifespan=lifespan)

allowed_origins = ["http://localhost:3000"]
if settings.VERCEL_URL:
    allowed_origins.append(f"https://{settings.VERCEL_URL}")
if settings.APP_URL:
    allowed_origins.append(settings.APP_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router.router, prefix="/api")
app.include_router(saved_router.router, prefix="/api")
app.include_router(searches_router.router, prefix="/api")
app.include_router(scan_router.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Jobs API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
