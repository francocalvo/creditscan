"""Extraction prompt and JSON schema for LLM-based statement parsing."""

EXTRACTION_PROMPT = """Fill the following JSON Schema from the PDF attached. ONLY answer with the JSON.
Don't add any text nor comments. Check very carefully for all the required data
in the schema, as it's completely needed.

Follow these indications:

- There are transactions that are calculated in function of another, like
  interests, taxes and fees. When this happens, you will the more than a number
  for that transaction. Try to guess which one is the correct one you have to
  consider. Normally it's the smaller one.
- Sometimes, the installments are embedded in the description of the
  transaction, like "ARG(1/12)", where the parenthesis show that is the current
  installment and total installments.
- The start date of the next cycle has to always be greater than the end date of
  the current cycle. If it's the same, probably the start date of the next cycle
  is the _next_ date after the end of the current cycle.

JSON Schema:
"""

EXTRACTION_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": [
        "statement_id",
        "period",
        "current_balance",
        "transactions",
    ],
    "properties": {
        "statement_id": {
            "type": "string",
            "description": "Unique identifier for the statement",
        },
        "card": {
            "type": "object",
            "properties": {
                "last_four": {
                    "type": "string",
                    "description": "Last 4 digits of card number",
                },
                "holder_name": {
                    "type": "string",
                    "description": "Name on the card",
                },
            },
        },
        "period": {
            "type": "object",
            "required": ["start", "end", "due_date"],
            "properties": {
                "start": {
                    "type": "string",
                    "format": "date",
                    "description": "Cycle start date (YYYY-MM-DD)",
                },
                "end": {
                    "type": "string",
                    "format": "date",
                    "description": "Cycle end date (YYYY-MM-DD)",
                },
                "due_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Payment due date (YYYY-MM-DD)",
                },
                "next_cycle_start": {
                    "type": "string",
                    "format": "date",
                    "description": "Next cycle start date (YYYY-MM-DD)",
                },
            },
        },
        "previous_balance": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["amount", "currency"],
                "properties": {
                    "amount": {"type": "number"},
                    "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                },
            },
        },
        "current_balance": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["amount", "currency"],
                "properties": {
                    "amount": {"type": "number"},
                    "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                },
            },
        },
        "minimum_payment": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["amount", "currency"],
                "properties": {
                    "amount": {"type": "number"},
                    "currency": {"type": "string", "minLength": 3, "maxLength": 3},
                },
            },
        },
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["date", "merchant", "amount"],
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "Transaction date (YYYY-MM-DD)",
                    },
                    "merchant": {
                        "type": "string",
                        "description": "Merchant or transaction description",
                    },
                    "coupon": {
                        "type": "string",
                        "description": "Coupon or reference number",
                    },
                    "amount": {
                        "type": "object",
                        "required": ["amount", "currency"],
                        "properties": {
                            "amount": {"type": "number"},
                            "currency": {
                                "type": "string",
                                "minLength": 3,
                                "maxLength": 3,
                            },
                        },
                    },
                    "installment": {
                        "type": "object",
                        "properties": {
                            "current": {
                                "type": "integer",
                                "description": "Current installment number",
                            },
                            "total": {
                                "type": "integer",
                                "description": "Total number of installments",
                            },
                        },
                    },
                },
            },
        },
    },
}
