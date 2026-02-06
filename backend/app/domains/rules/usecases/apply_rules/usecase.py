"""Usecase for applying rules to transactions."""

import uuid

from sqlmodel import Session

from app.domains.rules.domain.models import (
    ApplyRulesRequest,
    ApplyRulesResponse,
    RuleMatch,
    TransactionMatch,
)
from app.domains.rules.repository import RuleRepository
from app.domains.rules.repository import provide as provide_rule_repo
from app.domains.rules.service import RuleEvaluationService, provide_rule_evaluation
from app.domains.tags.domain.errors import TagNotFoundError
from app.domains.tags.repository import TagRepository
from app.domains.tags.repository import provide as provide_tag_repo
from app.domains.transaction_tags.domain.models import TransactionTagCreate
from app.domains.transaction_tags.repository import (
    TransactionTagRepository,
)
from app.domains.transaction_tags.repository import (
    provide as provide_transaction_tag_repo,
)
from app.domains.transactions.domain.models import Transaction
from app.domains.transactions.repository import (
    TransactionRepository,
)
from app.domains.transactions.repository import (
    provide as provide_transaction_repo,
)


class ApplyRulesUseCase:
    """Usecase for evaluating rules and applying tags to transactions."""

    def __init__(
        self,
        rule_repo: RuleRepository,
        transaction_repo: TransactionRepository,
        tag_repo: TagRepository,
        transaction_tag_repo: TransactionTagRepository,
        evaluation_service: RuleEvaluationService,
    ) -> None:
        """Initialize the usecase with dependencies."""
        self.rule_repo = rule_repo
        self.transaction_repo = transaction_repo
        self.tag_repo = tag_repo
        self.transaction_tag_repo = transaction_tag_repo
        self.evaluation_service = evaluation_service

    def execute(
        self, user_id: uuid.UUID, request: ApplyRulesRequest
    ) -> ApplyRulesResponse:
        """Execute the usecase to apply rules.

        Args:
            user_id: The ID of the user whose rules to apply.
            request: The apply rules request with optional statement_id and transaction_ids.

        Returns:
            ApplyRulesResponse: Response with processed transactions, tags applied, and details.
        """
        # Step 1: Fetch active rules for user
        rules = self.rule_repo.list(
            filters={"user_id": user_id, "is_active": True}, limit=10000
        )

        # If no active rules, return empty response
        if not rules:
            return ApplyRulesResponse(
                transactions_processed=0, tags_applied=0, details=[]
            )

        # Step 2: Determine transactions to process
        transactions: list[Transaction] = []

        if request.transaction_ids:
            # Fetch specific transactions, verifying ownership
            for tx_id in request.transaction_ids:
                transaction = self.transaction_repo.get_by_id_for_user(tx_id, user_id)
                if transaction:
                    transactions.append(transaction)
                # Skip transactions that don't exist or don't belong to user
        elif request.statement_id:
            # Fetch all transactions for the statement, verifying ownership
            # Note: statement_id filtering is passed to list_for_user
            transactions = self.transaction_repo.list_for_user(
                user_id=user_id,
                filters={"statement_id": request.statement_id},
                limit=10000,
            )
        else:
            # No scope defined: apply to all user transactions
            transactions = self.transaction_repo.list_for_user(
                user_id=user_id,
                limit=10000,
            )

        # Step 3: Process each transaction
        tags_applied_count = 0
        details: list[TransactionMatch] = []

        for transaction in transactions:
            matched_rules: list[RuleMatch] = []

            for rule in rules:
                # Evaluate rule against transaction
                if self.evaluation_service.evaluate_rule(rule, transaction):
                    applied_tags: list[uuid.UUID] = []

                    for action in rule.actions:
                        # Check if tag is soft-deleted
                        try:
                            tag = self.tag_repo.get_by_id(
                                action.tag_id, include_deleted=True
                            )
                            if tag.deleted_at is not None:
                                # Skip soft-deleted tags
                                continue
                        except TagNotFoundError:
                            # Tag doesn't exist, skip
                            continue

                        # Try to create transaction-tag relationship
                        result = self.transaction_tag_repo.create_or_ignore(
                            TransactionTagCreate(
                                transaction_id=transaction.id, tag_id=action.tag_id
                            )
                        )
                        if result is not None:
                            applied_tags.append(action.tag_id)
                            tags_applied_count += 1

                    # If any tags were applied, record the rule match
                    if applied_tags:
                        matched_rules.append(
                            RuleMatch(
                                rule_id=rule.rule_id,
                                rule_name=rule.name,
                                tags_applied=applied_tags,
                            )
                        )

            # If any rules matched, record the transaction match
            if matched_rules:
                details.append(
                    TransactionMatch(
                        transaction_id=transaction.id, matched_rules=matched_rules
                    )
                )

        # Step 4: Return response
        return ApplyRulesResponse(
            transactions_processed=len(transactions),
            tags_applied=tags_applied_count,
            details=details,
        )


def provide(session: Session) -> ApplyRulesUseCase:
    """Provide an instance of ApplyRulesUseCase.

    Args:
        session: The database session to use.

    Returns:
        ApplyRulesUseCase: An instance of ApplyRulesUseCase with dependencies injected.
    """
    return ApplyRulesUseCase(
        rule_repo=provide_rule_repo(session),
        transaction_repo=provide_transaction_repo(session),
        tag_repo=provide_tag_repo(session),
        transaction_tag_repo=provide_transaction_tag_repo(session),
        evaluation_service=provide_rule_evaluation(),
    )
