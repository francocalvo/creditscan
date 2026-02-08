"""Atomic import service for statement and transaction creation.

This module provides atomic (all-or-nothing) import operations for
statement data, ensuring that either both statement and transactions
are created, or neither is.
"""

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlmodel import Session

from app.domains.card_statements.domain.models import (
    CardStatement,
    CardStatementPublic,
    StatementStatus,
)
from app.domains.credit_cards.domain.models import (
    CreditCard,
    LimitSource,
)
from app.domains.transactions.domain.models import (
    Transaction,
    TransactionPublic,
)
from app.domains.upload_jobs.domain.errors import (
    CurrencyConversionError,
)
from app.pkgs.currency import provide as provide_currency
from app.pkgs.extraction.models import ExtractedStatement, Money

logger = logging.getLogger(__name__)


class AtomicImportService:
    """Service for atomic statement and transaction import.

    All operations in this service are performed within a single
    database transaction to ensure data consistency.
    """

    def __init__(self, session: Session):
        """Initialize with database session.

        Args:
            session: Database session for transaction management
        """
        self.session = session
        self.currency_service = provide_currency()

    def _transaction_context(self):
        """Return a transaction context compatible with the current session state.

        If the session already has an active transaction, use a savepoint to avoid
        nested root transaction errors. Otherwise, start a regular transaction.
        """
        if self.session.in_transaction():
            return self.session.begin_nested()
        return self.session.begin()

    @staticmethod
    def _has_balance_mismatch(
        current_balance: Decimal | None,
        transactions_total: Decimal,
        tolerance: Decimal = Decimal("0.01"),
    ) -> bool:
        """Return True when current balance differs from transactions total."""
        if current_balance is None:
            return False
        return abs(current_balance - transactions_total) > tolerance

    async def import_statement_atomic(
        self,
        data: ExtractedStatement,
        card_id: uuid.UUID,
        target_currency: str,
        source_file_path: str,
    ) -> tuple[CardStatementPublic, list[TransactionPublic]]:
        """Atomically import statement and all transactions.

        This method creates both the statement and all its transactions
        within a single database transaction. If any part fails, the
        entire operation is rolled back.

        Args:
            data: Extracted statement data
            card_id: Credit card ID
            target_currency: Target currency for conversion
            source_file_path: Path to the stored PDF file

        Returns:
            Tuple of (created statement, list of created transactions)
        """
        # Use explicit transaction boundary for true atomicity
        with self._transaction_context():
            # Convert balances to target currency
            previous_balance = await self.currency_service.convert_balance(
                data.previous_balance or [], target_currency
            )
            current_balance = await self.currency_service.convert_balance(
                data.current_balance, target_currency
            )
            minimum_payment = await self.currency_service.convert_balance(
                data.minimum_payment or [], target_currency
            )
            transaction_money = [txn.amount for txn in data.transactions]
            transactions_total = (
                await self.currency_service.convert_balance(
                    transaction_money, target_currency
                )
                if transaction_money
                else Decimal("0")
            )
            statement_status = StatementStatus.COMPLETE
            if self._has_balance_mismatch(current_balance, transactions_total):
                statement_status = StatementStatus.PENDING_REVIEW
                logger.warning(
                    "Statement balance mismatch detected: "
                    "card_id=%s current_balance=%s transactions_total=%s currency=%s",
                    card_id,
                    current_balance,
                    transactions_total,
                    target_currency,
                )

            # Fetch card for potential limit update
            card = self.session.get(CreditCard, card_id)
            if card is None:
                logger.error(f"Card {card_id} not found during import")
                # Raise to fail the entire import (atomicity)
                raise ValueError(f"Card {card_id} not found")

            # Create statement within the transaction
            statement = CardStatement(
                card_id=card_id,
                period_start=data.period.start,
                period_end=data.period.end,
                close_date=data.period.end,
                due_date=data.period.due_date,
                previous_balance=previous_balance,
                current_balance=current_balance,
                minimum_payment=minimum_payment,
                currency=target_currency,
                status=statement_status,
                source_file_path=source_file_path,
            )
            self.session.add(statement)
            self.session.flush()  # Flush to get the statement ID

            # Update card's credit limit if appropriate
            await self._maybe_update_card_limit(
                card=card,
                extracted_limit=data.credit_limit,
                statement_period_end=data.period.end,
            )

            # Create all transactions
            transactions: list[Transaction] = []
            for txn in data.transactions:
                transaction = Transaction(
                    statement_id=statement.id,
                    txn_date=txn.date,
                    payee=txn.merchant,
                    description=txn.merchant,
                    amount=txn.amount.amount,
                    currency=txn.amount.currency,
                    coupon=txn.coupon,
                    installment_cur=txn.installment.current
                    if txn.installment
                    else None,
                    installment_tot=txn.installment.total if txn.installment else None,
                )
                self.session.add(transaction)
                transactions.append(transaction)

            self.session.flush()  # Flush to get transaction IDs

            # Refresh all objects to get their final state
            self.session.refresh(statement)
            for txn in transactions:
                self.session.refresh(txn)

            return (
                CardStatementPublic.model_validate(statement),
                [TransactionPublic.model_validate(t) for t in transactions],
            )

    async def import_partial_statement_atomic(
        self,
        partial_data: dict[str, object],
        card_id: uuid.UUID,
        target_currency: str,
        source_file_path: str,
    ) -> tuple[CardStatementPublic, list[TransactionPublic]]:
        """Atomically import partial statement data.

        Args:
            partial_data: Partially extracted data as dict
            card_id: Credit card ID
            target_currency: Target currency for conversion
            source_file_path: Path to the stored PDF file

        Returns:
            Tuple of (created statement, list of created transactions)
        """
        # Use explicit transaction boundary for true atomicity
        with self._transaction_context():
            # Safely extract period dates
            period = partial_data.get("period", {})
            period_start = self._extract_date(period.get("start"))
            period_end = self._extract_date(period.get("end"))
            due_date = self._extract_date(period.get("due_date"))

            # Safely extract balances
            previous_balance_amount = None
            current_balance_amount = None
            minimum_payment_amount = None

            if "previous_balance" in partial_data:
                previous_balance_amount = await self._safe_convert_balance(
                    partial_data.get("previous_balance"), target_currency
                )

            if "current_balance" in partial_data:
                current_balance_amount = await self._safe_convert_balance(
                    partial_data.get("current_balance"), target_currency
                )

            if "minimum_payment" in partial_data:
                minimum_payment_amount = await self._safe_convert_balance(
                    partial_data.get("minimum_payment"), target_currency
                )

            # Create statement with PENDING_REVIEW status
            statement = CardStatement(
                card_id=card_id,
                period_start=period_start,
                period_end=period_end,
                close_date=period_end,
                due_date=due_date,
                previous_balance=previous_balance_amount,
                current_balance=current_balance_amount,
                minimum_payment=minimum_payment_amount,
                currency=target_currency,
                status=StatementStatus.PENDING_REVIEW,
                source_file_path=source_file_path,
            )
            self.session.add(statement)
            self.session.flush()

            # Create transactions from partial data
            transactions: list[Transaction] = []
            raw_transactions = partial_data.get("transactions", [])
            if isinstance(raw_transactions, list):
                for i, raw_txn in enumerate(raw_transactions):
                    try:
                        if isinstance(raw_txn, dict):
                            txn_date = self._extract_date(raw_txn.get("date"))
                            merchant = raw_txn.get("merchant")
                            amount_data = raw_txn.get("amount")

                            if txn_date and merchant and isinstance(amount_data, dict):
                                amount = Decimal(str(amount_data.get("amount", 0)))
                                currency = str(amount_data.get("currency", "ARS"))

                                transaction = Transaction(
                                    statement_id=statement.id,
                                    txn_date=txn_date,
                                    payee=merchant,
                                    description=merchant,
                                    amount=amount,
                                    currency=currency,
                                    coupon=raw_txn.get("coupon"),
                                    installment_cur=self._extract_installment(
                                        raw_txn.get("installment"), "current"
                                    ),
                                    installment_tot=self._extract_installment(
                                        raw_txn.get("installment"), "total"
                                    ),
                                )
                                self.session.add(transaction)
                                transactions.append(transaction)
                            else:
                                logger.warning(
                                    f"Skipping transaction {i}: missing required fields"
                                )
                    except Exception as e:
                        logger.warning(f"Skipping transaction {i}: {e}")

            self.session.flush()

            # Refresh all objects
            self.session.refresh(statement)
            for txn in transactions:
                self.session.refresh(txn)

            return (
                CardStatementPublic.model_validate(statement),
                [TransactionPublic.model_validate(t) for t in transactions],
            )

    def _extract_date(self, value: object) -> date | None:
        """Safely extract date from various formats."""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                from datetime import datetime

                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    async def _safe_convert_balance(
        self,
        balance_data: object,
        target_currency: str,
    ) -> Decimal | None:
        """Safely convert balance data to target currency."""
        if not balance_data:
            return None

        try:
            if isinstance(balance_data, list):
                money_list = []
                for item in balance_data:
                    if isinstance(item, dict):
                        money = Money(
                            amount=Decimal(str(item.get("amount", 0))),
                            currency=str(item.get("currency", "ARS")),
                        )
                        money_list.append(money)
                if money_list:
                    return await self.currency_service.convert_balance(
                        money_list, target_currency
                    )
        except Exception as e:
            logger.warning(f"Failed to convert balance: {e}")
            return None

        return None

    def _extract_installment(self, installment_data: object, field: str) -> int | None:
        """Safely extract installment field."""
        if isinstance(installment_data, dict):
            value = installment_data.get(field)
            if isinstance(value, int):
                return value
        return None

    async def _convert_single_amount(
        self, amount: Decimal, from_currency: str, to_currency: str
    ) -> Decimal:
        """Convert a single amount from one currency to another.

        Wraps CurrencyService.convert_balance to handle single amounts.
        Note: This uses the current API rate, not date-based rates.
        When PR #10 merges, this should use date-based conversion.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Converted amount in target currency

        Raises:
            CurrencyConversionError: If conversion fails
        """
        if from_currency == to_currency:
            # Same currency, no conversion needed
            return amount.quantize(Decimal("0.01"))

        # Use CurrencyService by creating a single-item Money list
        money_list = [Money(amount=amount, currency=from_currency)]
        converted = await self.currency_service.convert_balance(money_list, to_currency)
        logger.info(f"Converted {amount} {from_currency} -> {converted} {to_currency}")
        return converted

    async def _maybe_update_card_limit(
        self,
        card: CreditCard,
        extracted_limit: Money | None,
        statement_period_end: date,
    ) -> None:
        """Update card's credit limit if appropriate.

        Updates the card's credit limit from the statement only if:
        1. Extracted limit is present and greater than 0
        2. Statement is newer than existing limit (by date)
        3. Currency conversion succeeds if needed

        If update occurs, sets limit_source to "statement" and
        limit_last_updated_at to the statement period end.

        Args:
            card: The credit card to potentially update
            extracted_limit: Credit limit extracted from statement (may be None)
            statement_period_end: The period end date of the statement
        """
        # Skip if no valid limit extracted
        if extracted_limit is None or extracted_limit.amount <= Decimal("0"):
            logger.info("Skipping limit update: extracted limit is null or zero")
            return

        # Check if we should update based on date
        should_update = (
            card.limit_last_updated_at is None
            or statement_period_end > card.limit_last_updated_at.date()
        )

        if not should_update:
            logger.info(
                f"Skipping limit update: statement date {statement_period_end} "
                f"is not newer than existing limit date {card.limit_last_updated_at}"
            )
            return

        # Determine the limit amount in card's currency
        if extracted_limit.currency != card.default_currency:
            try:
                # Try to convert to card's currency
                # Note: Using current rate, not date-based (PR #10 pending)
                limit_in_card_currency = await self._convert_single_amount(
                    amount=extracted_limit.amount,
                    from_currency=extracted_limit.currency,
                    to_currency=card.default_currency,
                )
                logger.info(
                    f"Converted limit from {extracted_limit.currency} to "
                    f"{card.default_currency}: {limit_in_card_currency}"
                )
            except CurrencyConversionError as e:
                # Conversion failed - skip limit update silently
                logger.warning(
                    f"Could not convert credit limit from "
                    f"{extracted_limit.currency} to {card.default_currency}: {e}"
                )
                return
        else:
            # Same currency - use extracted amount directly
            limit_in_card_currency = extracted_limit.amount

        # Update the card's limit
        card.credit_limit = limit_in_card_currency
        card.limit_source = LimitSource.STATEMENT
        card.limit_last_updated_at = datetime.combine(
            statement_period_end, datetime.min.time()
        )

        logger.info(
            f"Updated card {card.id} limit to {limit_in_card_currency} "
            f"{card.default_currency} from statement (period: {statement_period_end})"
        )


def provide_atomic_import(session: Session) -> AtomicImportService:
    """Provider function for AtomicImportService.

    Args:
        session: Database session

    Returns:
        Configured AtomicImportService instance
    """
    return AtomicImportService(session)
