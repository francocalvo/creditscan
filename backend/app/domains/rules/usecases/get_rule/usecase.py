"""Usecase for getting a rule by ID."""

import uuid

from sqlmodel import Session

from app.domains.rules.domain.models import RulePublic
from app.domains.rules.service import RuleService, provide_rule_service


class GetRuleUseCase:
    """Usecase for getting a rule by ID."""

    def __init__(self, service: RuleService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> RulePublic:
        """Execute the usecase to get a rule.

        Args:
            rule_id: The ID of the rule to retrieve
            user_id: The ID of the user requesting the rule

        Returns:
            RulePublic: The rule data
        """
        return self.service.get_rule(rule_id, user_id)


def provide(session: Session) -> GetRuleUseCase:
    """Provide an instance of GetRuleUseCase.

    Args:
        session: The database session to use.
    """
    return GetRuleUseCase(provide_rule_service(session))
