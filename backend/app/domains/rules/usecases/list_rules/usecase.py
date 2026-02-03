"""Usecase for listing rules."""

import uuid

from sqlmodel import Session

from app.domains.rules.domain.models import RulesPublic
from app.domains.rules.service import RuleService, provide_rule_service


class ListRulesUseCase:
    """Usecase for listing rules with pagination."""

    def __init__(self, service: RuleService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> RulesPublic:
        """Execute the usecase to list rules.

        Args:
            user_id: The ID of the user whose rules to list
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            RulesPublic: Paginated rules data
        """
        return self.service.list_rules(user_id, skip=skip, limit=limit)


def provide(session: Session) -> ListRulesUseCase:
    """Provide an instance of ListRulesUseCase.

    Args:
        session: The database session to use.
    """
    return ListRulesUseCase(provide_rule_service(session))
