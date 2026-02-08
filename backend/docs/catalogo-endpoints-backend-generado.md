# Backend Endpoint Catalog (Generated)

Generated on: 2026-02-08

## `backend/app/api/routes/card_statements/create_statement.py`
- router_prefix: `/card-statements`
- tags: `"card-statements"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/card-statements/` | `create_card_statement` |

## `backend/app/api/routes/card_statements/delete_statement.py`
- router_prefix: `/card-statements`
- tags: `"card-statements"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/card-statements/{statement_id}` | `delete_card_statement` |

## `backend/app/api/routes/card_statements/get_statement.py`
- router_prefix: `/card-statements`
- tags: `"card-statements"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/card-statements/{statement_id}` | `get_card_statement` |

## `backend/app/api/routes/card_statements/list_statements.py`
- router_prefix: `/card-statements`
- tags: `"card-statements"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/card-statements/` | `list_card_statements` |

## `backend/app/api/routes/card_statements/update_statement.py`
- router_prefix: `/card-statements`
- tags: `"card-statements"`

| Method | Path | Handler |
|---|---|---|
| `PATCH` | `/card-statements/{statement_id}` | `update_card_statement` |

## `backend/app/api/routes/card_statements/upload_statement.py`
- router_prefix: `/card-statements`
- tags: `"card-statements"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/card-statements/upload` | `upload_statement` |

## `backend/app/api/routes/credit_cards/create_card.py`
- router_prefix: `/credit-cards`
- tags: `"credit-cards"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/credit-cards/` | `create_credit_card` |

## `backend/app/api/routes/credit_cards/delete_card.py`
- router_prefix: `/credit-cards`
- tags: `"credit-cards"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/credit-cards/{card_id}` | `delete_credit_card` |

## `backend/app/api/routes/credit_cards/get_card.py`
- router_prefix: `/credit-cards`
- tags: `"credit-cards"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/credit-cards/{card_id}` | `get_credit_card` |

## `backend/app/api/routes/credit_cards/list_cards.py`
- router_prefix: `/credit-cards`
- tags: `"credit-cards"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/credit-cards/` | `list_credit_cards` |

## `backend/app/api/routes/credit_cards/update_card.py`
- router_prefix: `/credit-cards`
- tags: `"credit-cards"`

| Method | Path | Handler |
|---|---|---|
| `PATCH` | `/credit-cards/{card_id}` | `update_credit_card` |

## `backend/app/api/routes/currency/convert.py`
- router_prefix: `/currency`
- tags: `"currency"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/currency/convert` | `convert_currency` |
| `POST` | `/currency/convert/batch` | `convert_currency_batch` |

## `backend/app/api/routes/currency/extract.py`
- router_prefix: `/currency`
- tags: `"currency"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/currency/rates/extract` | `trigger_extraction` |

## `backend/app/api/routes/currency/rates.py`
- router_prefix: `/currency`
- tags: `"currency"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/currency/rates` | `get_exchange_rates` |

## `backend/app/api/routes/login.py`
- router_prefix: ``
- tags: ``

| Method | Path | Handler |
|---|---|---|
| `POST` | `/login/access-token` | `login_access_token` |
| `POST` | `/login/test-token` | `test_token` |
| `POST` | `/password-recovery/{email}` | `recover_password` |
| `POST` | `/reset-password/` | `reset_password` |
| `POST` | `/password-recovery-html-content/{email}` | `recover_password_html_content` |

## `backend/app/api/routes/payments/create_payment.py`
- router_prefix: `/payments`
- tags: `"payments"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/payments/` | `create_payment` |

## `backend/app/api/routes/payments/delete_payment.py`
- router_prefix: `/payments`
- tags: `"payments"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/payments/{payment_id}` | `delete_payment` |

## `backend/app/api/routes/payments/get_payment.py`
- router_prefix: `/payments`
- tags: `"payments"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/payments/{payment_id}` | `get_payment` |

## `backend/app/api/routes/payments/list_payments.py`
- router_prefix: `/payments`
- tags: `"payments"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/payments/` | `list_payments` |

## `backend/app/api/routes/payments/update_payment.py`
- router_prefix: `/payments`
- tags: `"payments"`

| Method | Path | Handler |
|---|---|---|
| `PATCH` | `/payments/{payment_id}` | `update_payment` |

## `backend/app/api/routes/private.py`
- router_prefix: ``
- tags: ``

| Method | Path | Handler |
|---|---|---|
| `POST` | `/users/` | `create_user` |

## `backend/app/api/routes/rules/apply_rules.py`
- router_prefix: `/rules`
- tags: `"rules"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/rules/apply` | `apply_rules` |

## `backend/app/api/routes/rules/create_rule.py`
- router_prefix: `/rules`
- tags: `"rules"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/rules/` | `create_rule` |

## `backend/app/api/routes/rules/delete_rule.py`
- router_prefix: `/rules`
- tags: `"rules"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/rules/{rule_id}` | `delete_rule` |

## `backend/app/api/routes/rules/get_rule.py`
- router_prefix: `/rules`
- tags: `"rules"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/rules/{rule_id}` | `get_rule` |

## `backend/app/api/routes/rules/list_rules.py`
- router_prefix: `/rules`
- tags: `"rules"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/rules/` | `list_rules` |

## `backend/app/api/routes/rules/update_rule.py`
- router_prefix: `/rules`
- tags: `"rules"`

| Method | Path | Handler |
|---|---|---|
| `PUT` | `/rules/{rule_id}` | `update_rule` |

## `backend/app/api/routes/tags/create_tag.py`
- router_prefix: `/tags`
- tags: `"tags"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/tags/` | `create_tag` |

## `backend/app/api/routes/tags/delete_tag.py`
- router_prefix: `/tags`
- tags: `"tags"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/tags/{tag_id}` | `delete_tag` |

## `backend/app/api/routes/tags/get_tag.py`
- router_prefix: `/tags`
- tags: `"tags"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/tags/{tag_id}` | `get_tag` |

## `backend/app/api/routes/tags/list_tags.py`
- router_prefix: `/tags`
- tags: `"tags"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/tags/` | `list_tags` |

## `backend/app/api/routes/tags/update_tag.py`
- router_prefix: `/tags`
- tags: `"tags"`

| Method | Path | Handler |
|---|---|---|
| `PATCH` | `/tags/{tag_id}` | `update_tag` |

## `backend/app/api/routes/transaction_tags/add_tag.py`
- router_prefix: `/transaction-tags`
- tags: `"transaction-tags"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/transaction-tags/` | `add_tag_to_transaction` |

## `backend/app/api/routes/transaction_tags/get_tags.py`
- router_prefix: `/transaction-tags`
- tags: `"transaction-tags"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/transaction-tags/transaction/{transaction_id}` | `get_transaction_tags` |

## `backend/app/api/routes/transaction_tags/get_tags_batch.py`
- router_prefix: `/transaction-tags`
- tags: `"transaction-tags"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/transaction-tags/batch` | `get_transaction_tags_batch` |

## `backend/app/api/routes/transaction_tags/remove_tag.py`
- router_prefix: `/transaction-tags`
- tags: `"transaction-tags"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/transaction-tags/transaction/{transaction_id}/tag/{tag_id}` | `remove_tag_from_transaction` |

## `backend/app/api/routes/transactions/create_transaction.py`
- router_prefix: `/transactions`
- tags: `"transactions"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/transactions/` | `create_transaction` |

## `backend/app/api/routes/transactions/delete_transaction.py`
- router_prefix: `/transactions`
- tags: `"transactions"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/transactions/{transaction_id}` | `delete_transaction` |

## `backend/app/api/routes/transactions/get_transaction.py`
- router_prefix: `/transactions`
- tags: `"transactions"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/transactions/{transaction_id}` | `get_transaction` |

## `backend/app/api/routes/transactions/list_transactions.py`
- router_prefix: `/transactions`
- tags: `"transactions"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/transactions/` | `list_transactions` |

## `backend/app/api/routes/transactions/update_transaction.py`
- router_prefix: `/transactions`
- tags: `"transactions"`

| Method | Path | Handler |
|---|---|---|
| `PATCH` | `/transactions/{transaction_id}` | `update_transaction` |

## `backend/app/api/routes/upload_jobs/get_job.py`
- router_prefix: `/upload-jobs`
- tags: `"upload-jobs"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/upload-jobs/{job_id}` | `get_upload_job` |

## `backend/app/api/routes/users/create_user.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/users/` | `create_user` |

## `backend/app/api/routes/users/delete_me.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/users/me` | `delete_current_user` |

## `backend/app/api/routes/users/delete_user.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `DELETE` | `/users/{user_id}` | `delete_user_by_id` |

## `backend/app/api/routes/users/get_balance.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/users/me/balance` | `get_user_balance` |

## `backend/app/api/routes/users/get_me.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/users/me` | `get_current_user` |

## `backend/app/api/routes/users/get_user.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/users/{user_id}` | `get_user_by_id` |

## `backend/app/api/routes/users/list_users.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `GET` | `/users/` | `list_users` |

## `backend/app/api/routes/users/signup.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `POST` | `/users/signup` | `register_user` |

## `backend/app/api/routes/users/update_me.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `PATCH` | `/users/me` | `update_current_user` |

## `backend/app/api/routes/users/update_password_me.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `PATCH` | `/users/me/password` | `update_current_user_password` |

## `backend/app/api/routes/users/update_user.py`
- router_prefix: `/users`
- tags: `"users"`

| Method | Path | Handler |
|---|---|---|
| `PATCH` | `/users/{user_id}` | `update_user_by_id` |

## `backend/app/api/routes/utils.py`
- router_prefix: ``
- tags: ``

| Method | Path | Handler |
|---|---|---|
| `POST` | `/test-email/` | `test_email` |
| `GET` | `/health-check/` | `health_check` |
