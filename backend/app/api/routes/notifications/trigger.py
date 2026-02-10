from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.domains.notifications.service.ntfy_client import NtfyClient
from app.domains.notifications.usecases.send_due_notifications.usecase import provide

router = APIRouter()


class TriggerResponse(BaseModel):
    statements_found: int
    notification_sent: bool


@router.post("/trigger", response_model=TriggerResponse)
async def trigger_notification(
    session: SessionDep,
    current_user: CurrentUser,
) -> TriggerResponse:
    """Manually trigger due date notification check for the current user."""
    ntfy_client = NtfyClient(settings.NTFY_INTERNAL_URL)
    usecase = provide(
        session=session,
        ntfy_client=ntfy_client,
        ntfy_public_url=settings.NTFY_PUBLIC_URL,
    )
    result = await usecase.execute_for_user(current_user.id)
    return TriggerResponse(
        statements_found=result.statements_found,
        notification_sent=result.notification_sent,
    )
