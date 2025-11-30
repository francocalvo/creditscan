"""Usecase for getting user balance information."""

import uuid
from datetime import date
from decimal import Decimal

from app.domains.card_statements.repository import (
    provide as provide_card_statement_repository,
)
from app.domains.card_statements.repository.card_statement_repository import (
    CardStatementRepository,
)
from app.domains.payments.repository import provide as provide_payment_repository
from app.domains.payments.repository.payment_repository import PaymentRepository
from app.domains.transactions.repository import (
    provide as provide_transaction_repository,
)
from app.domains.transactions.repository.transaction_repository import (
    TransactionRepository,
)
from app.domains.users.domain.models import UserBalancePublic


class GetUserBalanceUseCase:
    """Usecase for getting user's total and monthly balance."""

    def __init__(
        self,
        statement_repository: CardStatementRepository,
        transaction_repository: TransactionRepository,
        payment_repository: PaymentRepository,
    ) -> None:
        """Initialize the usecase with repositories."""
        self.statement_repository = statement_repository
        self.transaction_repository = transaction_repository
        self.payment_repository = payment_repository

    def execute(self, user_id: uuid.UUID) -> UserBalancePublic:
        """Execute the usecase to calculate user balance.

        Args:
            user_id: UUID of the user

        Returns:
            UserBalancePublic: Balance information with total and monthly balances

        Logic:
            - Total balance: All transactions from unpaid/partially paid statements - all payments
            - Monthly balance: Same as total, but excludes future installments
        """
        # Get all statements that are not fully paid for this user
        unpaid_statements = self.statement_repository.list(
            skip=0,
            limit=10000,  # Get all unpaid statements
            filters={"user_id": user_id, "is_fully_paid": False},
        )

        if not unpaid_statements:
            # No unpaid statements, balance is zero
            return UserBalancePublic(total_balance=0.0, monthly_balance=0.0)

        # Get statement IDs
        statement_ids = [stmt.id for stmt in unpaid_statements]

        # Get all transactions for these statements
        all_transactions = []
        for statement_id in statement_ids:
            transactions = self.transaction_repository.list(
                skip=0, limit=10000, filters={"statement_id": statement_id}
            )
            all_transactions.extend(transactions)

        # Get all payments for these statements
        all_payments = []
        for statement_id in statement_ids:
            payments = self.payment_repository.list(
                skip=0, limit=10000, filters={"statement_id": statement_id}
            )
            all_payments.extend(payments)

        # Calculate total balance
        total_transactions = sum(
            (Decimal(str(txn.amount)) for txn in all_transactions), Decimal("0")
        )
        total_payments = sum(
            (Decimal(str(pmt.amount)) for pmt in all_payments), Decimal("0")
        )
        total_balance = total_transactions - total_payments

        # Calculate monthly balance (excluding future installments)
        today = date.today()
        monthly_transactions = Decimal("0")

        for txn in all_transactions:
            # If transaction has installments, check if it's a future installment
            if txn.installment_cur is not None and txn.installment_tot is not None:
                # Check if this is a future installment
                # Assuming txn_date represents when this installment is due
                # If the transaction date is in the future, it's a future installment
                if txn.txn_date > today:
                    # Skip future installments for monthly balance
                    continue

            monthly_transactions += Decimal(str(txn.amount))

        monthly_balance = monthly_transactions - total_payments

        return UserBalancePublic(
            total_balance=float(total_balance), monthly_balance=float(monthly_balance)
        )


def provide() -> GetUserBalanceUseCase:
    """Provide an instance of GetUserBalanceUseCase."""
    return GetUserBalanceUseCase(
        provide_card_statement_repository(),
        provide_transaction_repository(),
        provide_payment_repository(),
    )
