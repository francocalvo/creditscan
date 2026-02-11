from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.domains.currency.service.rate_scheduler import RateExtractionScheduler
from app.domains.notifications.service.notification_scheduler import (
    NotificationScheduler,
)
from app.domains.notifications.service.ntfy_client import NtfyClient
from app.domains.upload_jobs.service.job_resumption import resume_pending_jobs


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle app lifecycle events."""
    # Startup tasks
    await resume_pending_jobs()

    scheduler = RateExtractionScheduler(
        hour=settings.RATE_EXTRACTION_HOUR,
        minute=settings.RATE_EXTRACTION_MINUTE,
    )
    scheduler.start()

    notification_scheduler = NotificationScheduler(
        hour=settings.NOTIFICATION_HOUR,
        minute=settings.NOTIFICATION_MINUTE,
        ntfy_client_factory=lambda: NtfyClient(settings.NTFY_INTERNAL_URL),
    )
    notification_scheduler.start()

    yield

    # Shutdown tasks
    await scheduler.stop()
    await notification_scheduler.stop()


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
