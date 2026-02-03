"""Apply rules to transactions endpoint."""

from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.domains.rules.domain.models import ApplyRulesRequest, ApplyRulesResponse
from app.domains.rules.usecases.apply_rules import provide as provide_apply_rules

router = APIRouter()


@router.post("/apply", response_model=ApplyRulesResponse)
def apply_rules(
    session: SessionDep,
    request: ApplyRulesRequest,
    current_user: CurrentUser,
) -> Any:
    """Apply rules to transactions.

    Evaluates all active rules for the current user against the specified
    transactions. If a rule matches, its associated tags are applied.

    - If statement_id is provided, applies rules to all transactions in that statement
    - If transaction_ids is provided, applies rules to those specific transactions
    - If neither is provided, returns an empty response (no transactions to process)

    Returns details about which rules matched and which tags were applied.
    """
    usecase = provide_apply_rules(session)
    return usecase.execute(user_id=current_user.id, request=request)
