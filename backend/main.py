from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.routers import cats, health_records, reminders, reports, uploads, settings, actions, consultation, preventive_care, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="MeowHealth API",
    description="猫咪健康守护 Web 版后端 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cats.router, prefix="/api/v1")
app.include_router(health_records.router, prefix="/api/v1")
app.include_router(reminders.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(uploads.router)
app.include_router(settings.router, prefix="/api/v1")
app.include_router(actions.router, prefix="/api/v1")
app.include_router(consultation.router, prefix="/api/v1")
app.include_router(preventive_care.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to MeowHealth API 🐱", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
