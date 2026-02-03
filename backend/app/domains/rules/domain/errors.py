"""Rule domain errors."""


class RuleError(Exception):
    """Base exception for rule errors."""

    pass


class RuleNotFoundError(RuleError):
    """Raised when a rule is not found."""

    def __init__(self, rule_id: str) -> None:
        """Initialize with rule ID."""
        super().__init__(f"Rule {rule_id} not found")
        self.rule_id = rule_id


class InvalidRuleDataError(RuleError):
    """Raised when rule data is invalid."""

    pass


class RuleValidationError(InvalidRuleDataError):
    """Raised when rule validation fails."""

    pass


class InvalidConditionError(InvalidRuleDataError):
    """Raised when a condition is invalid."""

    pass


class InvalidActionError(InvalidRuleDataError):
    """Raised when an action is invalid."""

    pass


class TagNotFoundForActionError(InvalidActionError):
    """Raised when tag doesn't exist for rule action."""

    def __init__(self, tag_id: str) -> None:
        """Initialize with tag ID."""
        super().__init__(f"Tag {tag_id} not found for rule action")
        self.tag_id = tag_id
