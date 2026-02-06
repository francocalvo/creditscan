"""Get tags for multiple transactions in a single request."""

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.domains.transaction_tags.domain.models import TransactionTagPublic
from app.domains.transaction_tags.repository.transaction_tag_repository import (
    provide as provide_repo,
)

router = APIRouter()


class BatchTransactionTagsRequest(BaseModel):
    """Request body for batch fetching transaction tags."""

    transaction_ids: list[uuid.UUID]


@router.post("/batch", response_model=list[TransactionTagPublic])
def get_transaction_tags_batch(
    session: SessionDep,
    body: BatchTransactionTagsRequest,
    _current_user: CurrentUser,
) -> list[TransactionTagPublic]:
    """Get all tags for multiple transactions in a single request.

    Returns all transaction-tag mappings for the given transaction IDs.
    Requires authentication (current_user dependency enforces this).
    """
    repo = provide_repo(session)
    tags = repo.list_by_transactions(body.transaction_ids)
    return [TransactionTagPublic.model_validate(t) for t in tags]
