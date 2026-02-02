"""Get user balance endpoint."""

from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.domains.users.domain.models import UserBalancePublic
from app.domains.users.usecases import provide

router = APIRouter()


@router.get("/me/balance", response_model=UserBalancePublic)
def get_user_balance(session: SessionDep, current_user: CurrentUser) -> Any:
    """Get current user's balance information.

    Returns:
        UserBalancePublic: Contains total_balance and monthly_balance

    Logic:
        - Total balance: Sum of all transactions from unpaid/partially paid statements - all payments
        - Monthly balance: Same as total, but excludes transactions with future installment dates
    """
    usecase = provide(session)
    return usecase.execute(user_id=current_user.id)
