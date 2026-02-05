"""Exchange rate repository implementation."""

from datetime import date as Date

from sqlmodel import Session, select

from app.domains.currency.domain.models import ExchangeRate


class ExchangeRateRepository:
    """Repository for exchange rate CRUD operations."""

    def get_rate_for_date(
        self, session: Session, rate_date: Date
    ) -> ExchangeRate | None:
        """Exact date lookup.

        Args:
            session: Database session
            rate_date: Date to look up

        Returns:
            ExchangeRate if found, None otherwise
        """
        statement = select(ExchangeRate).where(ExchangeRate.rate_date == rate_date)
        return session.exec(statement).first()

    def get_closest_rate(
        self, session: Session, target_date: Date
    ) -> ExchangeRate | None:
        """Find closest rate, preferring earlier date if equidistant.

        Args:
            session: Database session
            target_date: Target date to find closest rate for

        Returns:
            ExchangeRate closest to target date, None if no rates exist
        """
        # Query for closest before and after
        before = session.exec(
            select(ExchangeRate)
            .where(ExchangeRate.rate_date <= target_date)
            .order_by(ExchangeRate.rate_date.desc())  # type: ignore
            .limit(1)
        ).first()

        after = session.exec(
            select(ExchangeRate)
            .where(ExchangeRate.rate_date > target_date)
            .order_by(ExchangeRate.rate_date.asc())  # type: ignore
            .limit(1)
        ).first()

        if not before and not after:
            return None
        if not before:
            return after
        if not after:
            return before

        # Compare distances, prefer earlier
        before_dist = (target_date - before.rate_date).days
        after_dist = (after.rate_date - target_date).days
        return before if before_dist <= after_dist else after

    def get_latest_rate(self, session: Session) -> ExchangeRate | None:
        """Get most recent rate.

        Args:
            session: Database session

        Returns:
            ExchangeRate with most recent rate_date, None if no rates exist
        """
        statement = (
            select(ExchangeRate).order_by(ExchangeRate.rate_date.desc()).limit(1)  # type: ignore
        )
        return session.exec(statement).first()

    def get_rates_in_range(
        self, session: Session, start: Date, end: Date
    ) -> list[ExchangeRate]:
        """Get all rates in date range inclusive.

        Args:
            session: Database session
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            List of ExchangeRate in the date range, sorted by date ascending
        """
        statement = (
            select(ExchangeRate)
            .where(ExchangeRate.rate_date >= start)
            .where(ExchangeRate.rate_date <= end)
            .order_by(ExchangeRate.rate_date.asc())  # type: ignore
        )
        return list(session.exec(statement).all())

    def upsert_rate(self, session: Session, rate: ExchangeRate) -> ExchangeRate:
        """Insert or update rate for a date.

        Args:
            session: Database session
            rate: ExchangeRate to insert or update

        Returns:
            The inserted or updated ExchangeRate
        """
        existing = self.get_rate_for_date(session, rate.rate_date)
        if existing:
            existing.buy_rate = rate.buy_rate
            existing.sell_rate = rate.sell_rate
            existing.source = rate.source
            existing.fetched_at = rate.fetched_at
            session.add(existing)
            return existing
        session.add(rate)
        return rate


def provide(_session: Session) -> ExchangeRateRepository:
    """Provide an instance of ExchangeRateRepository.

    Args:
        _session: The database session (unused; kept for DI consistency).

    Returns:
        ExchangeRateRepository: An instance of the repository.
    """
    return ExchangeRateRepository()
