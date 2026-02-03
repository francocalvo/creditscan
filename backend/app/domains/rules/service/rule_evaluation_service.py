"""Rule evaluation service for evaluating conditions against transactions."""

from datetime import date
from decimal import Decimal, InvalidOperation

from app.domains.rules.domain.errors import InvalidConditionError
from app.domains.rules.domain.models import (
    ConditionField,
    ConditionOperator,
    Rule,
    RuleCondition,
)
from app.domains.transactions.domain.models import Transaction


class RuleEvaluationService:
    """Service for evaluating rules against transactions."""

    def _get_field_value(
        self, transaction: Transaction, field: ConditionField
    ) -> str | Decimal | date | None:
        """Get the value of a field from a transaction.

        Args:
            transaction: The transaction to get the field value from.
            field: The field to retrieve.

        Returns:
            The value of the field, or None if not found.
        """
        field_mapping = {
            ConditionField.PAYEE: transaction.payee,
            ConditionField.DESCRIPTION: transaction.description,
            ConditionField.AMOUNT: transaction.amount,
            ConditionField.DATE: transaction.txn_date,
        }
        return field_mapping.get(field)

    def _parse_amount(self, value: str) -> Decimal | None:
        """Parse a string value as a Decimal.

        Args:
            value: The string value to parse.

        Returns:
            The parsed Decimal, or None if parsing fails.
        """
        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None

    def _parse_date(self, value: str) -> date | None:
        """Parse a string value as a date (ISO format).

        Args:
            value: The string value to parse.

        Returns:
            The parsed date, or None if parsing fails.
        """
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def evaluate_condition(
        self, condition: RuleCondition, transaction: Transaction
    ) -> bool:
        """Evaluate a single condition against a transaction.

        Args:
            condition: The condition to evaluate.
            transaction: The transaction to evaluate against.

        Returns:
            True if the condition matches, False otherwise.
        """
        field_value = self._get_field_value(transaction, condition.field)

        # Null/None field values are non-matches
        if field_value is None:
            return False

        operator = condition.operator

        # String operators: CONTAINS, EQUALS (for strings)
        if operator == ConditionOperator.CONTAINS:
            return condition.value.lower() in str(field_value).lower()

        if operator == ConditionOperator.EQUALS:
            # For strings, case-insensitive comparison
            if isinstance(field_value, str):
                return str(field_value).lower() == condition.value.lower()
            # For amounts, exact match after parsing
            if isinstance(field_value, Decimal):
                parsed = self._parse_amount(condition.value)
                if parsed is None:
                    return False
                return field_value == parsed
            # For dates, exact match after parsing
            if isinstance(field_value, date):
                parsed = self._parse_date(condition.value)
                if parsed is None:
                    return False
                return field_value == parsed
            return False

        # Numeric operators: GT, LT
        if operator == ConditionOperator.GT:
            if not isinstance(field_value, Decimal):
                return False
            parsed = self._parse_amount(condition.value)
            if parsed is None:
                return False
            return field_value > parsed

        if operator == ConditionOperator.LT:
            if not isinstance(field_value, Decimal):
                return False
            parsed = self._parse_amount(condition.value)
            if parsed is None:
                return False
            return field_value < parsed

        # Date operators: BEFORE, AFTER, BETWEEN
        if operator == ConditionOperator.BEFORE:
            if not isinstance(field_value, date):
                return False
            parsed = self._parse_date(condition.value)
            if parsed is None:
                return False
            return field_value < parsed

        if operator == ConditionOperator.AFTER:
            if not isinstance(field_value, date):
                return False
            parsed = self._parse_date(condition.value)
            if parsed is None:
                return False
            return field_value > parsed

        if operator == ConditionOperator.BETWEEN:
            if condition.value_secondary is None:
                raise InvalidConditionError(
                    "BETWEEN operator requires value_secondary to be set"
                )
            # BETWEEN works for dates and amounts
            if isinstance(field_value, date):
                start = self._parse_date(condition.value)
                end = self._parse_date(condition.value_secondary)
                if start is None or end is None:
                    return False
                return start <= field_value <= end
            if isinstance(field_value, Decimal):
                start = self._parse_amount(condition.value)
                end = self._parse_amount(condition.value_secondary)
                if start is None or end is None:
                    return False
                return start <= field_value <= end
            return False

        return False

    def evaluate_rule(self, rule: Rule, transaction: Transaction) -> bool:
        """Evaluate a rule against a transaction using left-to-right logic.

        Args:
            rule: The rule to evaluate.
            transaction: The transaction to evaluate against.

        Returns:
            True if the rule matches the transaction, False otherwise.
        """
        # Inactive rules don't match
        if not rule.is_active:
            return False

        # Sort conditions by position
        conditions = sorted(rule.conditions, key=lambda c: c.position)

        # Empty conditions means no match
        if not conditions:
            return False

        # First condition sets initial result
        result = self.evaluate_condition(conditions[0], transaction)

        # Apply subsequent conditions with their logical operators
        for condition in conditions[1:]:
            condition_result = self.evaluate_condition(condition, transaction)

            if condition.logical_operator.value == "AND":
                result = result and condition_result
            else:  # OR
                result = result or condition_result

        return result


def provide() -> RuleEvaluationService:
    """Provide an instance of RuleEvaluationService.

    Returns:
        RuleEvaluationService: An instance of RuleEvaluationService.
    """
    return RuleEvaluationService()
