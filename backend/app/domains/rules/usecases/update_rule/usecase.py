"""Usecase for updating a rule."""

import uuid

from sqlmodel import Session

from app.domains.rules.domain.models import RulePublic, RuleUpdate
from app.domains.rules.service import RuleService, provide_rule_service


class UpdateRuleUseCase:
    """Usecase for updating a rule."""

    def __init__(self, service: RuleService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self, rule_id: uuid.UUID, user_id: uuid.UUID, rule_data: RuleUpdate
    ) -> RulePublic:
        """Execute the usecase to update a rule.

        Args:
            rule_id: The ID of the rule to update
            user_id: The ID of the user updating the rule
            rule_data: The updated rule data

        Returns:
            RulePublic: The updated rule
        """
        return self.service.update_rule(rule_id, user_id, rule_data)


def provide(session: Session) -> UpdateRuleUseCase:
    """Provide an instance of UpdateRuleUseCase.

    Args:
        session: The database session to use.
    """
    return UpdateRuleUseCase(provide_rule_service(session))
