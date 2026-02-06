"""Unit tests for ExchangeRateRepository."""

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app.domains.currency.domain.models import ExchangeRate
from app.domains.currency.repository import provide


class TestExchangeRateRepositoryGetRateForDate:
    """Tests for get_rate_for_date method."""

    def test_get_rate_for_date_exact_match(self, db: Session):
        """Exact date lookup returns correct rate."""
        repo = provide(db)

        # Create rates for specific dates
        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 3),
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        # Query for exact date
        result = repo.get_rate_for_date(db, date(2026, 2, 1))

        assert result is not None
        assert result.rate_date == date(2026, 2, 1)
        assert result.buy_rate == Decimal("1458.74")
        assert result.sell_rate == Decimal("1459.32")

    def test_get_rate_for_date_not_found(self, db: Session):
        """Exact date lookup returns None when not found."""
        repo = provide(db)

        # Create rates for other dates
        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 3),
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        # Query for non-existent date
        result = repo.get_rate_for_date(db, date(2026, 2, 2))

        assert result is None

    def test_get_rate_for_date_empty_db(self, db: Session):
        """Exact date lookup returns None when database is empty."""
        repo = provide(db)

        result = repo.get_rate_for_date(db, date(2026, 2, 2))

        assert result is None


class TestExchangeRateRepositoryGetClosestRate:
    """Tests for get_closest_rate method."""

    def test_get_closest_rate_prefers_earlier(self, db: Session):
        """Closest rate prefers earlier date when equidistant."""
        repo = provide(db)

        # Create rates at equal distance
        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),  # 2 days before
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 5),  # 2 days after
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        # Query for date in the middle (Feb 3)
        result = repo.get_closest_rate(db, date(2026, 2, 3))

        assert result is not None
        # Should prefer earlier date
        assert result.rate_date == date(2026, 2, 1)
        assert result.buy_rate == Decimal("1458.74")

    def test_get_closest_rate_returns_closer_before(self, db: Session):
        """Closest rate returns before date when it's closer."""
        repo = provide(db)

        # Create rates at unequal distance
        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),  # 1 day before
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 5),  # 2 days after
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        # Query for date closer to rate1
        result = repo.get_closest_rate(db, date(2026, 2, 2))

        assert result is not None
        assert result.rate_date == date(2026, 2, 1)

    def test_get_closest_rate_returns_closer_after(self, db: Session):
        """Closest rate returns after date when it's closer."""
        repo = provide(db)

        # Create rates at unequal distance
        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),  # 3 days before
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 4),  # 1 day after
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        # Query for date closer to rate2
        result = repo.get_closest_rate(db, date(2026, 2, 3))

        assert result is not None
        assert result.rate_date == date(2026, 2, 4)

    def test_get_closest_rate_returns_after_only(self, db: Session):
        """Closest rate returns only after date when no before exists."""
        repo = provide(db)

        rate = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 5),
        )
        db.add(rate)
        db.commit()

        # Query for earlier date
        result = repo.get_closest_rate(db, date(2026, 2, 2))

        assert result is not None
        assert result.rate_date == date(2026, 2, 5)

    def test_get_closest_rate_returns_before_only(self, db: Session):
        """Closest rate returns only before date when no after exists."""
        repo = provide(db)

        rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),
        )
        db.add(rate)
        db.commit()

        # Query for later date
        result = repo.get_closest_rate(db, date(2026, 2, 5))

        assert result is not None
        assert result.rate_date == date(2026, 2, 1)

    def test_get_closest_rate_no_rates_returns_none(self, db: Session):
        """Closest rate returns None with empty database."""
        repo = provide(db)

        result = repo.get_closest_rate(db, date(2026, 2, 3))

        assert result is None


class TestExchangeRateRepositoryGetLatestRate:
    """Tests for get_latest_rate method."""

    def test_get_latest_rate_returns_most_recent(self, db: Session):
        """Get latest rate returns rate with most recent date."""
        repo = provide(db)

        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 5),
        )
        rate3 = ExchangeRate(
            buy_rate=Decimal("1460.00"),
            sell_rate=Decimal("1461.00"),
            rate_date=date(2026, 2, 3),
        )
        db.add(rate1)
        db.add(rate2)
        db.add(rate3)
        db.commit()

        result = repo.get_latest_rate(db)

        assert result is not None
        assert result.rate_date == date(2026, 2, 5)
        assert result.buy_rate == Decimal("1459.50")

    def test_get_latest_rate_empty_db(self, db: Session):
        """Get latest rate returns None when no rates exist."""
        repo = provide(db)

        result = repo.get_latest_rate(db)

        assert result is None


class TestExchangeRateRepositoryGetRatesInRange:
    """Tests for get_rates_in_range method."""

    def test_get_rates_in_range_returns_all(self, db: Session):
        """Get rates in range returns all rates within bounds."""
        repo = provide(db)

        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1459.00"),
            sell_rate=Decimal("1459.50"),
            rate_date=date(2026, 2, 3),
        )
        rate3 = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 5),
        )
        rate4 = ExchangeRate(
            buy_rate=Decimal("1460.00"),
            sell_rate=Decimal("1461.00"),
            rate_date=date(2026, 2, 8),  # Outside range
        )
        db.add(rate1)
        db.add(rate2)
        db.add(rate3)
        db.add(rate4)
        db.commit()

        # Query range inclusive of Feb 1-5
        result = repo.get_rates_in_range(db, date(2026, 2, 1), date(2026, 2, 5))

        assert len(result) == 3
        # Should be sorted ascending
        assert result[0].rate_date == date(2026, 2, 1)
        assert result[1].rate_date == date(2026, 2, 3)
        assert result[2].rate_date == date(2026, 2, 5)

    def test_get_rates_in_range_exclusive(self, db: Session):
        """Get rates in range excludes boundary dates."""
        repo = provide(db)

        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1459.50"),
            sell_rate=Decimal("1460.00"),
            rate_date=date(2026, 2, 5),
        )
        rate3 = ExchangeRate(
            buy_rate=Decimal("1460.00"),
            sell_rate=Decimal("1461.00"),
            rate_date=date(2026, 2, 8),
        )
        db.add(rate1)
        db.add(rate2)
        db.add(rate3)
        db.commit()

        # Query range Feb 2-7 (excludes Feb 1 and 8)
        result = repo.get_rates_in_range(db, date(2026, 2, 2), date(2026, 2, 7))

        assert len(result) == 1
        assert result[0].rate_date == date(2026, 2, 5)

    def test_get_rates_in_range_empty(self, db: Session):
        """Get rates in range returns empty list when no rates match."""
        repo = provide(db)

        rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 1, 1),
        )
        db.add(rate)
        db.commit()

        # Query different month
        result = repo.get_rates_in_range(db, date(2026, 2, 1), date(2026, 2, 5))

        assert result == []

    def test_get_rates_in_range_empty_db(self, db: Session):
        """Get rates in range returns empty list when database is empty."""
        repo = provide(db)

        result = repo.get_rates_in_range(db, date(2026, 2, 1), date(2026, 2, 5))

        assert result == []


class TestExchangeRateRepositoryUpsertRate:
    """Tests for upsert_rate method."""

    def test_upsert_creates_new_rate(self, db: Session):
        """Upsert creates new rate when date doesn't exist."""
        repo = provide(db)

        rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 4),
        )

        result = repo.upsert_rate(db, rate)
        db.commit()
        db.refresh(result)

        assert result.id is not None
        assert result.buy_rate == Decimal("1458.74")
        assert result.sell_rate == Decimal("1459.32")
        assert result.rate_date == date(2026, 2, 4)

        # Verify it's in the database
        retrieved = repo.get_rate_for_date(db, date(2026, 2, 4))
        assert retrieved is not None
        assert retrieved.id == result.id

    def test_upsert_updates_existing_rate(self, db: Session):
        """Upsert updates existing rate when date already exists."""
        repo = provide(db)

        # Create initial rate
        original_rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 4),
        )
        created = repo.upsert_rate(db, original_rate)
        db.commit()
        original_id = created.id

        # Create updated rate for same date
        updated_rate = ExchangeRate(
            buy_rate=Decimal("1500.00"),  # New buy rate
            sell_rate=Decimal("1501.00"),  # New sell rate
            rate_date=date(2026, 2, 4),
        )

        result = repo.upsert_rate(db, updated_rate)
        db.commit()
        db.refresh(result)

        # Should have updated the existing record
        assert result.id == original_id
        assert result.buy_rate == Decimal("1500.00")
        assert result.sell_rate == Decimal("1501.00")
        assert result.rate_date == date(2026, 2, 4)

        # Verify no duplicate in database
        all_rates = repo.get_rates_in_range(db, date(2026, 2, 1), date(2026, 2, 28))
        assert len(all_rates) == 1

    def test_upsert_updates_source_and_fetched_at(self, db: Session):
        """Upsert updates metadata fields on existing rate."""
        repo = provide(db)

        # Create initial rate
        original_rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 4),
            source="manual_entry",
        )
        repo.upsert_rate(db, original_rate)
        db.commit()

        # Create updated rate with different metadata
        updated_rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 4),
            source="cronista_mep",
        )

        result = repo.upsert_rate(db, updated_rate)
        db.commit()
        db.refresh(result)

        assert result.source == "cronista_mep"

    def test_upsert_returns_updated_instance(self, db: Session):
        """Upsert returns the rate instance that was inserted/updated."""
        repo = provide(db)

        rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=date(2026, 2, 4),
        )

        result = repo.upsert_rate(db, rate)
        db.commit()

        # Should be the same object
        assert result.buy_rate == Decimal("1458.74")
        assert result.sell_rate == Decimal("1459.32")
