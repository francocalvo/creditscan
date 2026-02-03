"""Usecase for deleting a rule."""

import uuid

from sqlmodel import Session

from app.domains.rules.service import RuleService, provide_rule_service


class DeleteRuleUseCase:
    """Usecase for deleting a rule."""

    def __init__(self, service: RuleService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Execute the usecase to delete a rule.

        Args:
            rule_id: The ID of the rule to delete
            user_id: The ID of the user deleting the rule
        """
        self.service.delete_rule(rule_id, user_id)


def provide(session: Session) -> DeleteRuleUseCase:
    """Provide an instance of DeleteRuleUseCase.

    Args:
        session: The database session to use.
    """
    return DeleteRuleUseCase(provide_rule_service(session))
