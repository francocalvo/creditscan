import logging
import uuid
from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import Session, select

from app.domains.card_statements.domain.models import CardStatement
from app.domains.credit_cards.domain.models import CreditCard
from app.domains.notifications.service.ntfy_client import NtfyClient
from app.domains.users.domain.models import User

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    user_id: uuid.UUID
    statements_found: int
    notification_sent: bool


class SendDueNotificationsUseCase:
    def __init__(
        self,
        session: Session,
        ntfy_client: NtfyClient,
        ntfy_public_url: str,
    ) -> None:
        self.session = session
        self.ntfy_client = ntfy_client
        self.ntfy_public_url = ntfy_public_url

    def _card_name(self, card: CreditCard) -> str:
        if card.alias:
            return card.alias
        return f"{card.brand.value.title()} ****{card.last4}"

    def _build_message(
        self, due_statements: list[tuple[CardStatement, CreditCard]]
    ) -> tuple[str, str]:
        if len(due_statements) == 1:
            stmt, card = due_statements[0]
            title = f"{self._card_name(card)}: Payment Due Tomorrow"
            body = f"Balance: ${stmt.current_balance:,.2f}"
            return title, body

        title = f"{len(due_statements)} Payments Due Tomorrow"
        lines = []
        for stmt, card in due_statements:
            lines.append(f"- {self._card_name(card)}: ${stmt.current_balance:,.2f}")
        body = "\n".join(lines)
        return title, body

    async def execute_for_user(self, user_id: uuid.UUID) -> SendResult:
        user = self.session.get(User, user_id)
        if not user:
            return SendResult(
                user_id=user_id, statements_found=0, notification_sent=False
            )

        tomorrow = date.today() + timedelta(days=1)

        statement = (
            select(CardStatement, CreditCard)
            .join(CreditCard, CardStatement.card_id == CreditCard.id)
            .where(
                CreditCard.user_id == user_id,
                CardStatement.due_date == tomorrow,
                CardStatement.is_fully_paid == False,  # noqa: E712
            )
        )
        results = self.session.exec(statement).all()

        if not results:
            return SendResult(
                user_id=user_id, statements_found=0, notification_sent=False
            )

        # Auto-generate topic if missing
        if not user.ntfy_topic:
            user.ntfy_topic = f"pf-app-{uuid.uuid4()}"
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

        title, body = self._build_message(results)
        sent = await self.ntfy_client.send(
            topic=user.ntfy_topic,
            title=title,
            message=body,
            priority=4,
            tags=["credit_card", "warning"],
        )

        return SendResult(
            user_id=user_id,
            statements_found=len(results),
            notification_sent=sent,
        )

    async def execute_all(self) -> list[SendResult]:
        users = self.session.exec(
            select(User).where(User.notifications_enabled == True)  # noqa: E712
        ).all()

        results = []
        for user in users:
            result = await self.execute_for_user(user.id)
            results.append(result)
            logger.info(
                "Notification result for user %s: %d statements, sent=%s",
                user.id,
                result.statements_found,
                result.notification_sent,
            )
        return results


def provide(
    session: Session,
    ntfy_client: NtfyClient,
    ntfy_public_url: str,
) -> SendDueNotificationsUseCase:
    return SendDueNotificationsUseCase(
        session=session,
        ntfy_client=ntfy_client,
        ntfy_public_url=ntfy_public_url,
    )
