"""Upload jobs routes module."""

from fastapi import APIRouter

from .get_job import router as get_job_router

router = APIRouter(prefix="/upload-jobs", tags=["upload-jobs"])

router.include_router(get_job_router)

__all__ = ["router"]
