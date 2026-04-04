import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Jobs API", version="0.1.0")

allowed_origins = ["http://localhost:3000"]
if vercel_url := os.getenv("VERCEL_URL"):
    allowed_origins.append(f"https://{vercel_url}")
if app_url := os.getenv("NEXT_PUBLIC_APP_URL"):
    allowed_origins.append(app_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Jobs API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
