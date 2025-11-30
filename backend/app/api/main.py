from fastapi import APIRouter

from app.api.routes import (
    card_statements,
    credit_cards,
    login,
    payments,
    private,
    tags,
    transaction_tags,
    transactions,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(credit_cards.router)
api_router.include_router(card_statements.router)
api_router.include_router(payments.router)
api_router.include_router(transactions.router)
api_router.include_router(tags.router)
api_router.include_router(transaction_tags.router)
api_router.include_router(utils.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
