"""Atomic import service for statement and transaction creation.

This module provides atomic (all-or-nothing) import operations for
statement data, ensuring that either both statement and transactions
are created, or neither is.
"""

import logging
import uuid
from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app.domains.card_statements.domain.models import (
    CardStatement,
    CardStatementPublic,
    StatementStatus,
)
from app.domains.transactions.domain.models import (
    Transaction,
    TransactionPublic,
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
        with self.session.begin():
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
                status=StatementStatus.COMPLETE,
                source_file_path=source_file_path,
            )
            self.session.add(statement)
            self.session.flush()  # Flush to get the statement ID

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
        with self.session.begin():
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


def provide_atomic_import(session: Session) -> AtomicImportService:
    """Provider function for AtomicImportService.

    Args:
        session: Database session

    Returns:
        Configured AtomicImportService instance
    """
    return AtomicImportService(session)
