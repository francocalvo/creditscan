"""Admin endpoint for triggering manual rate extraction."""

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.api.deps import CurrentUser
from app.domains.currency.domain.models import ExchangeRate
from app.domains.currency.repository.exchange_rate_repository import (
    provide as provide_repository,
)
from app.domains.currency.service.exchange_rate_extractor import (
    ExchangeRateExtractor,
    ExtractedRate,
)
from app.pkgs.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


async def run_extraction_job() -> None:
    """Background job to fetch and store the latest exchange rate.

    Creates its own database session, fetches rate from Cronista,
    upserts it to the database, and logs success or failure.
    """
    session = get_db_session()
    try:
        logger.info("Starting rate extraction job")

        # Fetch current rate from Cronista
        extractor = ExchangeRateExtractor()
        extracted_rate: ExtractedRate = await extractor.fetch_current_rate()

        logger.info(
            f"Extracted rate: buy={extracted_rate.buy_rate}, "
            f"sell={extracted_rate.sell_rate}, date={extracted_rate.rate_date}"
        )

        # Build ExchangeRate record
        exchange_rate = ExchangeRate(
            buy_rate=extracted_rate.buy_rate,
            sell_rate=extracted_rate.sell_rate,
            rate_date=extracted_rate.rate_date,
            source=extracted_rate.source,
            fetched_at=extracted_rate.fetched_at,
        )

        # Upsert to database
        repository = provide_repository(session)
        repository.upsert_rate(session, exchange_rate)

        # Commit transaction
        session.commit()
        logger.info(
            f"Successfully upserted exchange rate for {extracted_rate.rate_date}"
        )

    except Exception:
        logger.exception("Rate extraction job failed")
        raise
    finally:
        session.close()


@router.post("/rates/extract", status_code=202)
def trigger_extraction(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Trigger manual extraction of the latest Dólar MEP rate (admin only).

    Enqueues a background job that:
    1. Fetches the current rate from Cronista
    2. Upserts it to the exchange_rate table
    3. Logs success or failure

    The endpoint returns immediately with 202 Accepted while the
    extraction runs in the background.

    Returns:
        {"status": "extraction_started"}

    Raises:
        HTTPException(403): If user is not a superuser.
    """
    # Explicit access control check
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Enqueue background job
    background_tasks.add_task(run_extraction_job)

    return {"status": "extraction_started"}
