"""Usecase for creating a rule."""

import uuid

from sqlmodel import Session

from app.domains.rules.domain.models import RuleCreate, RulePublic
from app.domains.rules.service import RuleService, provide_rule_service


class CreateRuleUseCase:
    """Usecase for creating a rule."""

    def __init__(self, service: RuleService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, rule_data: RuleCreate, user_id: uuid.UUID) -> RulePublic:
        """Execute the usecase to create a rule.

        Args:
            rule_data: The rule data to create
            user_id: The ID of the user creating the rule

        Returns:
            RulePublic: The created rule
        """
        return self.service.create_rule(rule_data, user_id)


def provide(session: Session) -> CreateRuleUseCase:
    """Provide an instance of CreateRuleUseCase.

    Args:
        session: The database session to use.
    """
    return CreateRuleUseCase(provide_rule_service(session))
