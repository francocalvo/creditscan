"""Prompts and JSON schemas for OCR + statement extraction."""

OCR_PROMPT = """You are an OCR extraction engine.
Read the attached PDF and return ONLY a valid JSON object with this shape:
{
  "pages": [
    {"page": 1, "text": "..."}
  ]
}

Rules:
- Preserve page numbering (1-based).
- Preserve line breaks as they appear in the document.
- Do not summarize, translate, or normalize values.
- If a page is blank or unreadable, return empty text for that page.
"""

OCR_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["pages"],
    "properties": {
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["page", "text"],
                "properties": {
                    "page": {"type": "integer", "minimum": 1},
                    "text": {"type": "string"},
                },
            },
        }
    },
}

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
  the current cycle. If it's the same, probably the start date of the next date
  after the end of the current cycle.
- Look explicitly for credit-limit concepts and headings, including:
  "Límite de crédito", "Credit Limit", "Límite disponible", "Línea de crédito".
- Return the value in the schema field `credit_limit` as a Money object: amount
  as a plain number (no symbols/thousand separators) and currency as a 3-letter
  ISO code.
- Prefer the total line/limit amount (not "available credit") when both are
  present; if only an "available" value is present and it's not clearly the
  total limit, return null rather than guessing.
- Return null if no credible limit value is present.
- Infer currency from the statement context (balances/transactions) when
  possible; otherwise pick the most likely 3-letter code from nearby currency
  markers.

If you see there is a transaction like "ULTIMO PAGO", "PAGO RECIBIDO", "SU PAGO
EN PESOS", etc. which is negative, is an old payment and SHOULD NOT be conisdered.

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
        "credit_limit": {
            "type": ["object", "null"],
            "required": ["amount", "currency"],
            "properties": {
                "amount": {"type": "number"},
                "currency": {"type": "string", "minLength": 3, "maxLength": 3},
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
