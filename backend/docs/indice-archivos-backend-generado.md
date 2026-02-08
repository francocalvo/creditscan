# Backend File Index (Generated)

Generated on: 2026-02-08
Tracked files in backend (`rg --files backend`): 366
Python files indexed: 343

## Python Files and Top-Level Symbols

### `backend/tests/services/test_upload_job_service.py`
- kind: test
- classes: TestUploadJobServiceCreate, TestUploadJobServiceGet, TestUploadJobServiceUpdateStatus, TestUploadJobServiceIncrementRetry
- functions: create_test_user, create_test_credit_card

### `backend/tests/e2e/test_upload_workflow.py`
- kind: test
- classes: TestUploadWorkflowE2E, TestJobStatusE2E, TestFullUploadFlow
- functions: create_test_user, get_user_token_headers, create_test_credit_card, sample_pdf_content, create_mock_extraction_result, mock_currency_service, mock_storage_service

### `backend/tests/e2e/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/tests/api/routes/test_upload_jobs.py`
- kind: route, test
- classes: TestGetUploadJob
- functions: (none)

### `backend/tests/api/routes/card_statements/test_upload_statement.py`
- kind: route, test
- classes: TestUploadStatement
- functions: sample_pdf_content, sample_txt_content, large_pdf_content, mock_current_user, mock_superuser, mock_other_user, mock_card, mock_other_card, mock_upload_job

### `backend/tests/api/routes/card_statements/__init__.py`
- kind: route, test
- classes: (none)
- functions: (none)

### `backend/tests/api/routes/test_rules.py`
- kind: route, test
- classes: (none)
- functions: create_test_user, create_test_tag, test_create_rule_success, test_create_rule_missing_conditions_400, test_create_rule_missing_actions_400, test_create_rule_invalid_tag_400, test_list_rules_pagination, test_list_rules_user_isolation, test_get_rule_success, test_get_rule_not_found_404, test_create_rule_invalid_operator_for_field_400, test_create_rule_between_without_value_secondary_400, test_update_rule_success, test_delete_rule_success, test_delete_rule_not_found_404

### `backend/tests/api/routes/test_currency_extract.py`
- kind: route, test
- classes: TestCurrencyExtract, TestExtractionJob
- functions: (none)

### `backend/tests/api/routes/test_credit_cards.py`
- kind: route, test
- classes: (none)
- functions: create_test_credit_card, create_test_statement, test_update_credit_limit_success, test_update_credit_limit_validation, test_update_credit_limit_metadata_refresh, test_update_other_fields_leaves_limit_metadata_unchanged, test_update_credit_limit_null_does_not_set_manual_source, test_update_credit_card_not_found, test_get_card_outstanding_balance, test_list_cards_outstanding_balance

### `backend/tests/api/routes/test_transaction_tags.py`
- kind: route, test
- classes: TestGetTransactionTagsOwnership
- functions: create_test_user, get_user_token_headers, create_test_credit_card, create_test_statement, create_test_transaction, create_test_tag, create_test_transaction_tag

### `backend/tests/api/routes/test_private.py`
- kind: route, test
- classes: (none)
- functions: test_create_user

### `backend/tests/api/routes/test_users.py`
- kind: route, test
- classes: (none)
- functions: test_get_users_superuser_me, test_get_users_normal_user_me, test_create_user_new_email, test_get_existing_user, test_get_existing_user_current_user, test_get_existing_user_permissions_error, test_create_user_existing_username, test_create_user_by_normal_user, test_retrieve_users, test_update_user_me, test_update_user_me_preferred_currency, test_update_user_me_clear_preferred_currency, test_update_password_me, test_update_password_me_incorrect_password, test_update_user_me_email_exists, test_update_password_me_same_password_error, test_register_user, test_register_user_already_exists_error, test_update_user, test_update_user_not_exists, test_update_user_email_exists, test_delete_user_me, test_delete_user_me_as_superuser, test_delete_user_super_user, test_delete_user_not_found, test_delete_user_current_super_user_error, test_delete_user_without_privileges

### `backend/tests/api/routes/__init__.py`
- kind: route, test
- classes: (none)
- functions: (none)

### `backend/tests/api/routes/test_currency_convert.py`
- kind: route, test
- classes: TestCurrencyConvert
- functions: (none)

### `backend/tests/api/routes/test_currency_rates.py`
- kind: route, test
- classes: TestCurrencyRates
- functions: (none)

### `backend/tests/api/routes/test_login.py`
- kind: route, test
- classes: (none)
- functions: test_get_access_token, test_get_access_token_incorrect_password, test_use_access_token, test_recovery_password, test_recovery_password_user_not_exits, test_reset_password, test_reset_password_invalid_token

### `backend/tests/api/routes/test_list_transactions.py`
- kind: route, test
- classes: TestListTransactionsOwnership
- functions: create_test_user, get_user_token_headers, create_test_credit_card, create_test_statement, create_test_transaction

### `backend/tests/api/routes/test_apply_rules.py`
- kind: route, test
- classes: (none)
- functions: create_test_user, create_test_tag, create_test_credit_card, create_test_statement, create_test_transaction, get_authenticated_user, create_test_rule_with_condition, test_apply_rules_by_transaction_ids_success, test_apply_rules_by_statement_id_success, test_apply_rules_multiple_rules_match, test_apply_rules_multiple_tags_per_rule, test_apply_rules_empty_request_applies_to_all, test_apply_rules_no_matching_rules, test_apply_rules_no_active_rules, test_apply_rules_invalid_transaction_ids, test_apply_rules_idempotent, test_apply_rules_skips_soft_deleted_tags, test_apply_rules_user_isolation_transaction_ids, test_apply_rules_user_isolation_statement_id, test_apply_rules_response_format, test_create_transaction_auto_applies_rules, test_create_transaction_succeeds_when_no_rules, test_create_transaction_succeeds_when_rule_fails

### `backend/tests/api/test_currency.py`
- kind: test
- classes: TestCurrencyIntegration
- functions: mock_cronista_response, mock_httpx_client, patch_extraction_session, seed_rate

### `backend/tests/api/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/tests/test_lifespan.py`
- kind: test
- classes: (none)
- functions: test_lifespan_scheduler_start_stop

### `backend/tests/conftest.py`
- kind: test
- classes: (none)
- functions: set_sqlite_pragma, _patched_bind_processor, engine, db, client, superuser_token_headers, normal_user_token_headers

### `backend/tests/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/tests/domains/currency/test_exchange_rate_model.py`
- kind: domain, test
- classes: TestExchangeRateModel
- functions: (none)

### `backend/tests/crud/rules/test_rule_service.py`
- kind: test
- classes: TestCreateRule, TestGetRule, TestListRules, TestUpdateRule, TestDeleteRule, TestOperatorValidation
- functions: create_test_user, create_test_tag, get_service, create_valid_rule_data

### `backend/tests/domains/currency/test_rate_scheduler.py`
- kind: domain, test
- classes: TestRateExtractionScheduler
- functions: (none)

### `backend/tests/domains/currency/test_exchange_rate_repository.py`
- kind: domain, test
- classes: TestExchangeRateRepositoryGetRateForDate, TestExchangeRateRepositoryGetClosestRate, TestExchangeRateRepositoryGetLatestRate, TestExchangeRateRepositoryGetRatesInRange, TestExchangeRateRepositoryUpsertRate
- functions: (none)

### `backend/tests/domains/currency/test_exchange_rate_extractor.py`
- kind: domain, test
- classes: TestExtractedRate, TestExchangeRateExtractor
- functions: (none)

### `backend/tests/crud/rules/test_rule_evaluation_service.py`
- kind: test
- classes: TestContainsOperator, TestEqualsOperator, TestNumericOperators, TestDateOperators, TestRuleEvaluation, TestEdgeCases, TestZeroAndNegativeAmounts, TestEmptyStringEdgeCases
- functions: create_transaction, create_condition, create_rule

### `backend/tests/crud/rules/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/tests/crud/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/tests/crud/test_user.py`
- kind: test
- classes: (none)
- functions: test_create_user, test_authenticate_user, test_not_authenticate_user, test_check_if_user_is_active, test_check_if_user_is_active_inactive, test_check_if_user_is_superuser, test_check_if_user_is_superuser_normal_user, test_get_user, test_update_user

### `backend/tests/crud/test_tag.py`
- kind: test
- classes: (none)
- functions: create_test_user, test_delete_tag_sets_deleted_at_timestamp, test_list_excludes_deleted_tags, test_get_by_id_excludes_deleted_tags_by_default, test_get_by_id_with_include_deleted_returns_deleted_tags, test_count_excludes_deleted_tags, test_delete_already_deleted_tag_raises_error, test_update_deleted_tag_raises_error

### `backend/tests/integration/test_credit_limits_flow.py`
- kind: test
- classes: TestCreditLimitsFlow
- functions: create_test_user, get_user_token_headers, create_test_credit_card, create_statement_directly, sample_pdf_content, create_mock_extraction_result, mock_currency_service, mock_storage_service, mock_extraction_service

### `backend/tests/repositories/test_upload_job_repository.py`
- kind: test
- classes: TestUploadJobRepositoryCreate, TestUploadJobRepositoryGetById, TestUploadJobRepositoryGetByFileHash, TestUploadJobRepositoryUpdateStatus
- functions: create_test_user, create_test_credit_card

### `backend/tests/repositories/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/app/models.py`
- kind: misc
- classes: Message, Token, TokenPayload
- functions: (none)

### `backend/tests/models/test_card_statement_models.py`
- kind: test
- classes: TestStatementStatusEnum, TestCardStatementCurrency, TestCardStatementStatus, TestCardStatementSourceFilePath, TestCardStatementCreate, TestCardStatementUpdate, TestCardStatementTableModel
- functions: (none)

### `backend/tests/domains/upload_jobs/usecases/test_process_upload.py`
- kind: domain, test
- classes: TestSanitizedErrorMessages, TestAtomicImport, TestCreditLimitUpdate, TestProcessUploadJob, TestApplyRules
- functions: mock_session, mock_job_service, mock_extraction_service, mock_currency_service, atomic_import_service, ars_credit_card, mock_statement_service, mock_transaction_service, mock_card, _mock_statement, _mock_transaction, _mock_extracted_statement

### `backend/tests/models/test_upload_job_models.py`
- kind: test
- classes: TestUploadJobStatusEnum, TestUploadJobDefaults, TestUploadJobCreate, TestUploadJobPublic, TestUploadJobErrors, TestUploadJobTableModel
- functions: (none)

### `backend/tests/models/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/tests/domains/upload_jobs/usecases/__init__.py`
- kind: domain, test
- classes: (none)
- functions: (none)

### `backend/app/services/__init__.py`
- kind: misc
- classes: (none)
- functions: (none)

### `backend/app/main.py`
- kind: misc
- classes: (none)
- functions: lifespan, custom_generate_unique_id

### `backend/app/tests_pre_start.py`
- kind: misc
- classes: (none)
- functions: init, main

### `backend/app/core/__init__.py`
- kind: misc
- classes: (none)
- functions: (none)

### `backend/tests/pkgs/currency/test_client.py`
- kind: test, pkg
- classes: TestExchangeRateClient
- functions: (none)

### `backend/app/core/security.py`
- kind: misc
- classes: (none)
- functions: create_access_token, verify_password, get_password_hash

### `backend/tests/pkgs/currency/__init__.py`
- kind: test, pkg
- classes: (none)
- functions: (none)

### `backend/tests/pkgs/currency/test_service.py`
- kind: test, pkg
- classes: TestCurrencyService, TestProvide
- functions: (none)

### `backend/app/core/config.py`
- kind: misc
- classes: Settings
- functions: parse_cors

### `backend/app/core/db.py`
- kind: misc
- classes: (none)
- functions: init_db

### `backend/app/__init__.py`
- kind: misc
- classes: (none)
- functions: (none)

### `backend/app/constants.py`
- kind: misc
- classes: (none)
- functions: (none)

### `backend/app/initial_data.py`
- kind: misc
- classes: (none)
- functions: init, main

### `backend/app/backend_pre_start.py`
- kind: misc
- classes: (none)
- functions: init, main

### `backend/app/pkgs/currency/__init__.py`
- kind: pkg
- classes: (none)
- functions: (none)

### `backend/app/pkgs/currency/client.py`
- kind: pkg
- classes: ExchangeRateClient
- functions: (none)

### `backend/app/pkgs/currency/service.py`
- kind: pkg
- classes: CurrencyService
- functions: provide

### `backend/app/pkgs/storage/__init__.py`
- kind: pkg
- classes: (none)
- functions: (none)

### `backend/app/pkgs/storage/client.py`
- kind: pkg
- classes: StorageClient
- functions: (none)

### `backend/app/pkgs/storage/service.py`
- kind: pkg
- classes: StorageService
- functions: provide

### `backend/tests/domains/credit_cards/test_credit_card_models.py`
- kind: domain, test
- classes: TestLimitSource, TestCreditCardLimitFields, TestCreditCardDefaultCurrency, TestCreditCardAlias
- functions: (none)

### `backend/tests/domains/credit_cards/test_credit_card_repository.py`
- kind: domain, test
- classes: TestCreditCardRepositoryOutstandingBalance
- functions: create_test_user, create_test_credit_card, create_test_statement

### `backend/tests/domains/credit_cards/__init__.py`
- kind: domain, test
- classes: (none)
- functions: (none)

### `backend/app/alembic/env.py`
- kind: misc
- classes: (none)
- functions: get_url, run_migrations_offline, run_migrations_online

### `backend/tests/pkgs/extraction/__init__.py`
- kind: test, pkg
- classes: (none)
- functions: (none)

### `backend/tests/pkgs/extraction/test_client.py`
- kind: test, pkg
- classes: TestOpenRouterClient
- functions: (none)

### `backend/tests/pkgs/extraction/test_models.py`
- kind: test, pkg
- classes: TestMoney, TestInstallmentInfo, TestExtractedTransaction, TestExtractedCycle, TestExtractedCard, TestExtractedStatement, TestExtractionResult
- functions: (none)

### `backend/tests/pkgs/extraction/test_service.py`
- kind: test, pkg
- classes: TestExtractionService, TestProvideFunction
- functions: (none)

### `backend/app/domains/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/tests/scripts/test_test_pre_start.py`
- kind: test
- classes: (none)
- functions: test_init_successful_connection

### `backend/tests/scripts/test_backend_pre_start.py`
- kind: test
- classes: (none)
- functions: test_init_successful_connection

### `backend/tests/scripts/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/tests/utils/utils.py`
- kind: test
- classes: (none)
- functions: random_lower_string, random_email, get_superuser_token_headers

### `backend/tests/utils/__init__.py`
- kind: test
- classes: (none)
- functions: (none)

### `backend/tests/utils/user.py`
- kind: test
- classes: (none)
- functions: user_authentication_headers, create_random_user, authentication_token_from_email

### `backend/app/utils.py`
- kind: misc
- classes: EmailData
- functions: render_email_template, send_email, generate_test_email, generate_reset_password_email, generate_new_account_email, generate_password_reset_token, verify_password_reset_token

### `backend/app/pkgs/extraction/service.py`
- kind: pkg
- classes: ExtractionService
- functions: provide

### `backend/app/pkgs/extraction/prompt.py`
- kind: pkg
- classes: (none)
- functions: (none)

### `backend/app/pkgs/extraction/__init__.py`
- kind: pkg
- classes: (none)
- functions: (none)

### `backend/app/pkgs/extraction/client.py`
- kind: pkg
- classes: OpenRouterClient
- functions: (none)

### `backend/tests/pkgs/storage/test_storage.py`
- kind: test, pkg
- classes: TestStorageClient, TestStorageService, TestProvideFunction
- functions: (none)

### `backend/app/pkgs/database/__init__.py`
- kind: pkg
- classes: (none)
- functions: (none)

### `backend/app/pkgs/database/provider.py`
- kind: pkg
- classes: (none)
- functions: get_engine, set_engine, get_db, get_db_session

### `backend/app/api/__init__.py`
- kind: misc
- classes: (none)
- functions: (none)

### `backend/app/api/deps.py`
- kind: misc
- classes: (none)
- functions: get_current_user, get_current_active_superuser

### `backend/app/api/main.py`
- kind: misc
- classes: (none)
- functions: (none)

### `backend/app/pkgs/extraction/models.py`
- kind: pkg
- classes: Money, InstallmentInfo, ExtractedTransaction, ExtractedCycle, ExtractedCard, ExtractedStatement, ExtractionResult
- functions: (none)

### `backend/app/domains/accounts/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/usecases/update_statement/usecase.py`
- kind: domain
- classes: UpdateCardStatementUseCase
- functions: provide

### `backend/app/domains/payments/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/usecases/update_statement/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/usecases/list_statements/usecase.py`
- kind: domain
- classes: ListCardStatementsUseCase
- functions: provide

### `backend/app/domains/card_statements/usecases/list_statements/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/upload_jobs/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/payments/repository/payment_repository.py`
- kind: domain
- classes: PaymentRepository
- functions: provide

### `backend/app/domains/payments/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/api/routes/card_statements/delete_statement.py`
- kind: route
- classes: (none)
- functions: delete_card_statement

### `backend/app/api/routes/card_statements/get_statement.py`
- kind: route
- classes: (none)
- functions: get_card_statement

### `backend/app/api/routes/card_statements/update_statement.py`
- kind: route
- classes: (none)
- functions: update_card_statement

### `backend/app/api/routes/card_statements/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/card_statements/create_statement.py`
- kind: route
- classes: (none)
- functions: create_card_statement

### `backend/app/api/routes/card_statements/list_statements.py`
- kind: route
- classes: (none)
- functions: list_card_statements

### `backend/app/api/routes/card_statements/upload_statement.py`
- kind: route
- classes: (none)
- functions: upload_statement

### `backend/app/api/routes/private.py`
- kind: route
- classes: PrivateUserCreate
- functions: create_user

### `backend/app/domains/transaction_tags/usecases/remove_tag/usecase.py`
- kind: domain
- classes: RemoveTagFromTransactionUseCase
- functions: provide

### `backend/app/domains/transaction_tags/usecases/remove_tag/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/usecases/create_statement/usecase.py`
- kind: domain
- classes: CreateCardStatementUseCase
- functions: provide

### `backend/app/domains/card_statements/usecases/create_statement/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/accounts/domain/models.py`
- kind: domain
- classes: AccountBase, AccountCreate, Account, AccountPublic, AccountsPublic
- functions: (none)

### `backend/app/domains/card_statements/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/payments/usecases/create_payment/usecase.py`
- kind: domain
- classes: CreatePaymentUseCase
- functions: provide

### `backend/app/domains/payments/usecases/create_payment/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/upload_jobs/usecases/process_upload/usecase.py`
- kind: domain
- classes: (none)
- functions: _import_with_atomic_service, _apply_rules_to_statement, _get_sanitized_error_message, process_upload_job

### `backend/app/domains/upload_jobs/usecases/process_upload/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transaction_tags/usecases/get_tags/usecase.py`
- kind: domain
- classes: GetTransactionTagsUseCase
- functions: provide

### `backend/app/domains/card_statements/usecases/get_statement/usecase.py`
- kind: domain
- classes: GetCardStatementUseCase
- functions: provide

### `backend/app/domains/card_statements/usecases/get_statement/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transaction_tags/usecases/get_tags/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/payments/domain/errors.py`
- kind: domain
- classes: PaymentNotFoundError
- functions: (none)

### `backend/app/domains/payments/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/payments/domain/models.py`
- kind: domain
- classes: PaymentBase, PaymentCreate, Payment, PaymentPublic, PaymentUpdate, PaymentsPublic
- functions: (none)

### `backend/app/domains/tags/usecases/list_tags/usecase.py`
- kind: domain
- classes: ListTagsUseCase
- functions: provide

### `backend/app/domains/tags/usecases/list_tags/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/usecases/list_transactions/usecase.py`
- kind: domain
- classes: ListTransactionsUseCase
- functions: provide

### `backend/app/domains/transactions/usecases/list_transactions/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/api/routes/currency/rates.py`
- kind: route
- classes: (none)
- functions: get_exchange_rates

### `backend/app/api/routes/currency/extract.py`
- kind: route
- classes: (none)
- functions: run_extraction_job, trigger_extraction

### `backend/app/api/routes/currency/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/currency/convert.py`
- kind: route
- classes: (none)
- functions: convert_currency, convert_currency_batch

### `backend/app/api/routes/login.py`
- kind: route
- classes: (none)
- functions: login_access_token, test_token, recover_password, reset_password, recover_password_html_content

### `backend/app/domains/payments/usecases/list_payments/usecase.py`
- kind: domain
- classes: ListPaymentsUseCase
- functions: provide

### `backend/app/domains/payments/usecases/list_payments/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/repository/card_statement_repository.py`
- kind: domain
- classes: CardStatementRepository
- functions: provide

### `backend/app/domains/upload_jobs/domain/errors.py`
- kind: domain
- classes: UploadJobError, UploadJobNotFoundError, DuplicateFileError, ExtractionError, CurrencyConversionError, StorageError, RulesApplicationError
- functions: (none)

### `backend/app/domains/upload_jobs/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/upload_jobs/domain/models.py`
- kind: domain
- classes: UploadJobStatus, UploadJob, UploadJobCreate, UploadJobPublic
- functions: (none)

### `backend/app/domains/payments/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/payments/service/payment_service.py`
- kind: domain
- classes: PaymentService
- functions: provide

### `backend/app/domains/payments/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/usecases/delete_statement/usecase.py`
- kind: domain
- classes: DeleteCardStatementUseCase
- functions: provide

### `backend/app/domains/card_statements/usecases/delete_statement/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/payments/usecases/update_payment/usecase.py`
- kind: domain
- classes: UpdatePaymentUseCase
- functions: provide

### `backend/app/domains/payments/usecases/update_payment/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transaction_tags/usecases/add_tag/usecase.py`
- kind: domain
- classes: AddTagToTransactionUseCase
- functions: provide

### `backend/app/domains/transaction_tags/usecases/add_tag/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transaction_tags/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/payments/usecases/delete_payment/usecase.py`
- kind: domain
- classes: DeletePaymentUseCase
- functions: provide

### `backend/app/domains/payments/usecases/delete_payment/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/usecases/get_transaction/usecase.py`
- kind: domain
- classes: GetTransactionUseCase
- functions: provide

### `backend/app/domains/tags/usecases/delete_tag/usecase.py`
- kind: domain
- classes: DeleteTagUseCase
- functions: provide

### `backend/app/domains/transactions/usecases/get_transaction/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/usecases/delete_tag/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/api/routes/rules/list_rules.py`
- kind: route
- classes: (none)
- functions: list_rules

### `backend/app/api/routes/rules/create_rule.py`
- kind: route
- classes: (none)
- functions: create_rule

### `backend/app/api/routes/rules/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/rules/apply_rules.py`
- kind: route
- classes: (none)
- functions: apply_rules

### `backend/app/api/routes/rules/update_rule.py`
- kind: route
- classes: (none)
- functions: update_rule

### `backend/app/api/routes/rules/get_rule.py`
- kind: route
- classes: (none)
- functions: get_rule

### `backend/app/api/routes/rules/delete_rule.py`
- kind: route
- classes: (none)
- functions: delete_rule

### `backend/app/domains/card_statements/domain/errors.py`
- kind: domain
- classes: CardStatementError, CardStatementNotFoundError, InvalidCardStatementDataError
- functions: (none)

### `backend/app/domains/card_statements/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transaction_tags/domain/errors.py`
- kind: domain
- classes: TransactionTagError, TransactionTagNotFoundError, InvalidTransactionTagDataError
- functions: (none)

### `backend/app/domains/transaction_tags/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/domain/models.py`
- kind: domain
- classes: StatementStatus, CardStatementBase, CardStatementCreate, CardStatement, CardStatementPublic, CardStatementUpdate, CardStatementsPublic
- functions: (none)

### `backend/app/domains/transaction_tags/domain/models.py`
- kind: domain
- classes: TransactionTag, TransactionTagCreate, TransactionTagPublic
- functions: (none)

### `backend/app/domains/card_statements/domain/options.py`
- kind: domain
- classes: SortOrder, SearchFilters, SearchPagination, SearchSorting, SearchOptions
- functions: (none)

### `backend/app/domains/transactions/domain/errors.py`
- kind: domain
- classes: TransactionError, TransactionNotFoundError, InvalidTransactionDataError
- functions: (none)

### `backend/app/domains/transactions/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/domain/models.py`
- kind: domain
- classes: TransactionBase, TransactionCreate, Transaction, TransactionPublic, TransactionUpdate, TransactionsPublic
- functions: (none)

### `backend/app/domains/transactions/domain/options.py`
- kind: domain
- classes: SortOrder, SearchFilters, SearchPagination, SearchSorting, SearchOptions
- functions: (none)

### `backend/app/domains/upload_jobs/service/atomic_import.py`
- kind: domain
- classes: AtomicImportService
- functions: provide_atomic_import

### `backend/app/domains/upload_jobs/service/upload_job_service.py`
- kind: domain
- classes: UploadJobService
- functions: provide

### `backend/app/domains/upload_jobs/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/upload_jobs/service/job_resumption.py`
- kind: domain
- classes: (none)
- functions: get_db_session_for_resumption, resume_pending_jobs

### `backend/app/domains/upload_jobs/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/payments/usecases/get_payment/usecase.py`
- kind: domain
- classes: GetPaymentUseCase
- functions: provide

### `backend/app/domains/payments/usecases/get_payment/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/usecases/delete_transaction/usecase.py`
- kind: domain
- classes: DeleteTransactionUseCase
- functions: provide

### `backend/app/domains/transactions/usecases/delete_transaction/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/usecases/create_transaction/usecase.py`
- kind: domain
- classes: CreateTransactionUseCase
- functions: provide

### `backend/app/domains/transactions/usecases/create_transaction/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/usecases/update_tag/usecase.py`
- kind: domain
- classes: UpdateTagUseCase
- functions: provide

### `backend/app/domains/tags/usecases/update_tag/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/api/routes/users/list_users.py`
- kind: route
- classes: (none)
- functions: list_users

### `backend/app/api/routes/users/get_me.py`
- kind: route
- classes: (none)
- functions: get_current_user

### `backend/app/api/routes/users/update_user.py`
- kind: route
- classes: (none)
- functions: update_user_by_id

### `backend/app/api/routes/users/get_user.py`
- kind: route
- classes: (none)
- functions: get_user_by_id

### `backend/app/api/routes/users/delete_user.py`
- kind: route
- classes: (none)
- functions: delete_user_by_id

### `backend/app/api/routes/users/update_me.py`
- kind: route
- classes: (none)
- functions: update_current_user

### `backend/app/api/routes/users/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/users/delete_me.py`
- kind: route
- classes: (none)
- functions: delete_current_user

### `backend/app/api/routes/users/get_balance.py`
- kind: route
- classes: (none)
- functions: get_user_balance

### `backend/app/api/routes/users/signup.py`
- kind: route
- classes: (none)
- functions: register_user

### `backend/app/api/routes/users/create_user.py`
- kind: route
- classes: (none)
- functions: create_user

### `backend/app/api/routes/users/update_password_me.py`
- kind: route
- classes: (none)
- functions: update_current_user_password

### `backend/app/api/routes/utils.py`
- kind: route
- classes: (none)
- functions: test_email, health_check

### `backend/app/domains/transactions/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/card_statements/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transaction_tags/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/service/transaction_service.py`
- kind: domain
- classes: TransactionService
- functions: provide

### `backend/app/domains/transaction_tags/service/transaction_tag_service.py`
- kind: domain
- classes: TransactionTagService
- functions: provide

### `backend/app/domains/card_statements/service/card_statement_service.py`
- kind: domain
- classes: CardStatementService
- functions: provide

### `backend/app/domains/transaction_tags/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/currency/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/upload_jobs/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/upload_jobs/repository/upload_job_repository.py`
- kind: domain
- classes: UploadJobRepository
- functions: provide

### `backend/app/domains/transactions/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transactions/repository/transaction_repository.py`
- kind: domain
- classes: TransactionRepository
- functions: provide

### `backend/app/domains/transaction_tags/repository/transaction_tag_repository.py`
- kind: domain
- classes: TransactionTagRepository
- functions: provide

### `backend/app/domains/tags/usecases/get_tag/usecase.py`
- kind: domain
- classes: GetTagUseCase
- functions: provide

### `backend/app/domains/tags/usecases/get_tag/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/transaction_tags/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/api/routes/transactions/update_transaction.py`
- kind: route
- classes: (none)
- functions: update_transaction

### `backend/app/api/routes/transactions/delete_transaction.py`
- kind: route
- classes: (none)
- functions: delete_transaction

### `backend/app/api/routes/transactions/list_transactions.py`
- kind: route
- classes: (none)
- functions: list_transactions

### `backend/app/api/routes/transactions/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/transactions/get_transaction.py`
- kind: route
- classes: (none)
- functions: get_transaction

### `backend/app/api/routes/transactions/create_transaction.py`
- kind: route
- classes: (none)
- functions: create_transaction

### `backend/app/domains/currency/usecases/convert_currency/usecase.py`
- kind: domain
- classes: ConvertCurrencyUseCase
- functions: provide

### `backend/app/domains/currency/usecases/convert_currency/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/currency/repository/exchange_rate_repository.py`
- kind: domain
- classes: ExchangeRateRepository
- functions: provide

### `backend/app/domains/currency/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/domain/errors.py`
- kind: domain
- classes: TagError, TagNotFoundError, InvalidTagDataError
- functions: (none)

### `backend/app/domains/currency/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/domain/models.py`
- kind: domain
- classes: TagBase, TagCreate, Tag, TagPublic, TagUpdate, TagsPublic
- functions: (none)

### `backend/app/domains/transactions/usecases/update_transaction/usecase.py`
- kind: domain
- classes: UpdateTransactionUseCase
- functions: provide

### `backend/app/domains/transactions/usecases/update_transaction/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/usecases/create_tag/usecase.py`
- kind: domain
- classes: CreateTagUseCase
- functions: provide

### `backend/app/domains/tags/usecases/create_tag/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/api/routes/transaction_tags/add_tag.py`
- kind: route
- classes: (none)
- functions: add_tag_to_transaction

### `backend/app/api/routes/transaction_tags/get_tags.py`
- kind: route
- classes: (none)
- functions: get_transaction_tags

### `backend/app/api/routes/transaction_tags/remove_tag.py`
- kind: route
- classes: (none)
- functions: remove_tag_from_transaction

### `backend/app/api/routes/transaction_tags/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/transaction_tags/get_tags_batch.py`
- kind: route
- classes: BatchTransactionTagsRequest
- functions: get_transaction_tags_batch

### `backend/app/api/routes/tags/list_tags.py`
- kind: route
- classes: (none)
- functions: list_tags

### `backend/app/api/routes/tags/get_tag.py`
- kind: route
- classes: (none)
- functions: get_tag

### `backend/app/api/routes/tags/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/tags/create_tag.py`
- kind: route
- classes: (none)
- functions: create_tag

### `backend/app/api/routes/tags/update_tag.py`
- kind: route
- classes: (none)
- functions: update_tag

### `backend/app/api/routes/tags/delete_tag.py`
- kind: route
- classes: (none)
- functions: delete_tag

### `backend/app/domains/currency/usecases/convert_currency_batch/usecase.py`
- kind: domain
- classes: ConvertCurrencyBatchUseCase
- functions: provide

### `backend/app/domains/currency/usecases/convert_currency_batch/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/service/tag_service.py`
- kind: domain
- classes: TagService
- functions: provide

### `backend/app/domains/credit_cards/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/tags/repository/tag_repository.py`
- kind: domain
- classes: TagRepository
- functions: provide

### `backend/app/domains/users/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/currency/service/rate_scheduler.py`
- kind: domain
- classes: RateExtractionScheduler
- functions: (none)

### `backend/app/domains/currency/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/currency/service/exchange_rate_extractor.py`
- kind: domain
- classes: ExtractedRate, ExchangeRateExtractor
- functions: (none)

### `backend/app/domains/currency/service/currency_conversion_service.py`
- kind: domain
- classes: CurrencyConversionService
- functions: provide

### `backend/app/api/routes/payments/delete_payment.py`
- kind: route
- classes: (none)
- functions: delete_payment

### `backend/app/api/routes/payments/create_payment.py`
- kind: route
- classes: (none)
- functions: create_payment

### `backend/app/api/routes/payments/update_payment.py`
- kind: route
- classes: (none)
- functions: update_payment

### `backend/app/api/routes/payments/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/payments/list_payments.py`
- kind: route
- classes: (none)
- functions: list_payments

### `backend/app/api/routes/payments/get_payment.py`
- kind: route
- classes: (none)
- functions: get_payment

### `backend/app/api/routes/upload_jobs/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/upload_jobs/get_job.py`
- kind: route
- classes: (none)
- functions: get_upload_job

### `backend/app/api/routes/credit_cards/list_cards.py`
- kind: route
- classes: (none)
- functions: list_credit_cards

### `backend/app/domains/users/usecases/get_balance/usecase.py`
- kind: domain
- classes: GetUserBalanceUseCase
- functions: provide

### `backend/app/api/routes/credit_cards/create_card.py`
- kind: route
- classes: (none)
- functions: create_credit_card

### `backend/app/api/routes/credit_cards/__init__.py`
- kind: route
- classes: (none)
- functions: (none)

### `backend/app/api/routes/credit_cards/update_card.py`
- kind: route
- classes: (none)
- functions: update_credit_card

### `backend/app/api/routes/credit_cards/delete_card.py`
- kind: route
- classes: (none)
- functions: delete_credit_card

### `backend/app/api/routes/credit_cards/get_card.py`
- kind: route
- classes: (none)
- functions: get_credit_card

### `backend/app/domains/credit_cards/domain/errors.py`
- kind: domain
- classes: CreditCardError, CreditCardNotFoundError, InvalidCreditCardDataError
- functions: (none)

### `backend/app/domains/credit_cards/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/credit_cards/domain/models.py`
- kind: domain
- classes: CardBrand, LimitSource, CreditCardBase, CreditCardCreate, CreditCard, CreditCardPublic, CreditCardUpdate, CreditCardsPublic
- functions: (none)

### `backend/app/domains/users/usecases/get_balance/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/currency/domain/errors.py`
- kind: domain
- classes: CurrencyError, UnsupportedCurrencyError, RateNotFoundError, ExtractionError
- functions: (none)

### `backend/app/domains/currency/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/currency/domain/models.py`
- kind: domain
- classes: CurrencyConversionRequest, CurrencyConversionResponse, BatchCurrencyConversionRequest, BatchCurrencyConversionResponse, ExchangeRatePublic, ExchangeRatesResponse, ExchangeRate
- functions: (none)

### `backend/app/domains/credit_cards/repository/credit_card_repository.py`
- kind: domain
- classes: CreditCardRepository
- functions: provide

### `backend/app/domains/credit_cards/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/domain/errors.py`
- kind: domain
- classes: UserError, UserNotFoundError, InvalidUserDataError, InvalidCredentialsError, DuplicateUserError
- functions: (none)

### `backend/app/domains/users/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/domain/models.py`
- kind: domain
- classes: UserBase, UserCreate, UserRegister, UserUpdate, UserUpdateMe, UpdatePassword, User, UserPublic, UsersPublic, NewPassword, UserBalancePublic
- functions: (none)

### `backend/app/domains/users/domain/options.py`
- kind: domain
- classes: SortOrder, SearchFilters, SearchPagination, SearchSorting, SearchOptions
- functions: (none)

### `backend/app/domains/users/repository/user_repository.py`
- kind: domain
- classes: UserRepository
- functions: provide

### `backend/app/domains/users/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/usecases/update_user/usecase.py`
- kind: domain
- classes: UpdateUserUseCase
- functions: provide

### `backend/app/domains/users/usecases/update_user/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/credit_cards/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/usecases/update_password/usecase.py`
- kind: domain
- classes: UpdatePasswordUseCase
- functions: provide

### `backend/app/domains/users/usecases/update_password/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/credit_cards/usecases/get_card/usecase.py`
- kind: domain
- classes: GetCreditCardUseCase
- functions: provide

### `backend/app/domains/credit_cards/usecases/get_card/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/usecases/delete_user/usecase.py`
- kind: domain
- classes: DeleteUserUseCase
- functions: provide

### `backend/app/domains/users/service/user_service.py`
- kind: domain
- classes: UserService
- functions: provide

### `backend/app/domains/users/usecases/delete_user/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/credit_cards/service/credit_card_service.py`
- kind: domain
- classes: CreditCardService
- functions: provide

### `backend/app/domains/credit_cards/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/usecases/create_rule/usecase.py`
- kind: domain
- classes: CreateRuleUseCase
- functions: provide

### `backend/app/domains/rules/usecases/create_rule/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/credit_cards/usecases/delete_card/usecase.py`
- kind: domain
- classes: DeleteCreditCardUseCase
- functions: provide

### `backend/app/domains/credit_cards/usecases/update_card/usecase.py`
- kind: domain
- classes: UpdateCreditCardUseCase
- functions: provide

### `backend/app/domains/credit_cards/usecases/create_card/usecase.py`
- kind: domain
- classes: CreateCreditCardUseCase
- functions: provide

### `backend/app/domains/credit_cards/usecases/delete_card/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/credit_cards/usecases/update_card/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/credit_cards/usecases/create_card/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/usecases/search_users/usecase.py`
- kind: domain
- classes: SearchUsersUseCase
- functions: provide

### `backend/app/domains/users/usecases/search_users/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/usecases/list_rules/usecase.py`
- kind: domain
- classes: ListRulesUseCase
- functions: provide

### `backend/app/domains/rules/usecases/list_rules/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/usecases/register_user/usecase.py`
- kind: domain
- classes: RegisterUserUseCase
- functions: provide

### `backend/app/domains/users/usecases/register_user/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/service/rule_evaluation_service.py`
- kind: domain
- classes: RuleEvaluationService
- functions: provide

### `backend/app/domains/rules/service/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/service/rule_service.py`
- kind: domain
- classes: RuleService
- functions: provide

### `backend/app/domains/rules/usecases/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/repository/rule_repository.py`
- kind: domain
- classes: RuleRepository
- functions: provide

### `backend/app/domains/rules/repository/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/usecases/delete_rule/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/usecases/apply_rules/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/usecases/create_user/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/usecases/delete_rule/usecase.py`
- kind: domain
- classes: DeleteRuleUseCase
- functions: provide

### `backend/app/domains/rules/usecases/apply_rules/usecase.py`
- kind: domain
- classes: ApplyRulesUseCase
- functions: provide

### `backend/app/domains/users/usecases/create_user/usecase.py`
- kind: domain
- classes: CreateUserUseCase
- functions: provide

### `backend/app/domains/rules/domain/models.py`
- kind: domain
- classes: ConditionField, ConditionOperator, LogicalOperator, ActionType, RuleBase, Rule, RuleCondition, RuleAction, RuleConditionCreate, RuleActionCreate, RuleCreate, RuleConditionPublic, RuleActionPublic, RulePublic, RulesPublic, RuleUpdate, RuleMatch, TransactionMatch, ApplyRulesRequest, ApplyRulesResponse
- functions: (none)

### `backend/app/domains/rules/usecases/get_rule/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/domain/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/usecases/get_rule/usecase.py`
- kind: domain
- classes: GetRuleUseCase
- functions: provide

### `backend/app/domains/rules/usecases/update_rule/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/rules/domain/errors.py`
- kind: domain
- classes: RuleError, RuleNotFoundError, InvalidRuleDataError, RuleValidationError, InvalidConditionError, InvalidActionError, TagNotFoundForActionError
- functions: (none)

### `backend/app/domains/rules/usecases/update_rule/usecase.py`
- kind: domain
- classes: UpdateRuleUseCase
- functions: provide

### `backend/app/domains/credit_cards/usecases/list_cards/usecase.py`
- kind: domain
- classes: ListCreditCardsUseCase
- functions: provide

### `backend/app/domains/credit_cards/usecases/list_cards/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)

### `backend/app/domains/users/usecases/authenticate_user/usecase.py`
- kind: domain
- classes: AuthenticateUserUseCase
- functions: provide

### `backend/app/domains/users/usecases/authenticate_user/__init__.py`
- kind: domain
- classes: (none)
- functions: (none)
