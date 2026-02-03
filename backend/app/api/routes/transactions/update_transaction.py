"""Update transaction endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases.get_statement import (
    provide as provide_get_statement,
)
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card
from app.domains.transactions.domain.errors import (
    InvalidTransactionDataError,
    TransactionNotFoundError,
)
from app.domains.transactions.domain.models import (
    TransactionPublic,
    TransactionUpdate,
)
from app.domains.transactions.usecases.get_transaction import (
    provide as provide_get_transaction,
)
from app.domains.transactions.usecases.update_transaction import (
    provide as provide_update_transaction,
)

router = APIRouter()


@router.patch("/{transaction_id}", response_model=TransactionPublic)
def update_transaction(
    session: SessionDep,
    transaction_id: uuid.UUID,
    transaction_in: TransactionUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a transaction.

    Users can only update transactions for statements they own.
    Superusers can update any transaction.
    """
    try:
        # First, check if the transaction exists and verify ownership
        get_transaction_usecase = provide_get_transaction(session)
        existing_transaction = get_transaction_usecase.execute(transaction_id)

        # Verify ownership through the statement
        get_statement_usecase = provide_get_statement(session)
        statement = get_statement_usecase.execute(existing_transaction.statement_id)

        get_card_usecase = provide_get_card(session)
        card = get_card_usecase.execute(statement.card_id)

        if card.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this transaction",
            )

        # Update the transaction
        update_usecase = provide_update_transaction(session)
        return update_usecase.execute(transaction_id, transaction_in)
    except TransactionNotFoundError:
        raise HTTPException(status_code=404, detail="Transaction not found")
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
    except CreditCardNotFoundError:
        raise HTTPException(status_code=404, detail="Credit card not found")
    except InvalidTransactionDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
