"""Create transaction endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.repository import (
    provide as provide_card_statement_repo,
)
from app.domains.credit_cards.repository import provide as provide_credit_card_repo
from app.domains.rules.domain.models import ApplyRulesRequest
from app.domains.rules.usecases.apply_rules import provide as provide_apply_rules
from app.domains.transactions.domain.errors import InvalidTransactionDataError
from app.domains.transactions.domain.models import (
    TransactionCreate,
    TransactionPublic,
)
from app.domains.transactions.usecases.create_transaction import (
    provide as provide_create_transaction,
)

router = APIRouter()


@router.post("/", response_model=TransactionPublic, status_code=201)
def create_transaction(
    session: SessionDep,
    transaction_in: TransactionCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new transaction.

    Users can only create transactions for statements they own.
    Superusers can create transactions for any statement.
    """
    try:
        # Verify that the statement exists and belongs to the user
        card_statement_repo = provide_card_statement_repo(session)
        statement = card_statement_repo.get_by_id(transaction_in.statement_id)

        # Get the credit card to check ownership
        credit_card_repo = provide_credit_card_repo(session)
        card = credit_card_repo.get_by_id(statement.card_id)

        if card.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to create transactions for this statement",
            )

        # Create the transaction
        usecase = provide_create_transaction(session)
        transaction = usecase.execute(transaction_in)

        # Apply rules to the newly created transaction
        # Wrapped in try-except: rule application failure should not fail transaction creation
        try:
            apply_rules_usecase = provide_apply_rules(session)
            apply_request = ApplyRulesRequest(transaction_ids=[transaction.id])
            apply_rules_usecase.execute(current_user.id, apply_request)
        except Exception:
            # Log but don't fail - transaction was created successfully
            # TODO: Add logging in production
            pass

        return transaction
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
    except InvalidTransactionDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
