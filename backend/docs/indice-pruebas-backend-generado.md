# Backend Test Index (Generated)

Generated on: 2026-02-08
Test files: 58

## `backend/tests/__init__.py`
- test_functions: 0

## `backend/tests/api/__init__.py`
- test_functions: 0

## `backend/tests/api/routes/__init__.py`
- test_functions: 0

## `backend/tests/api/routes/card_statements/__init__.py`
- test_functions: 0

## `backend/tests/api/routes/card_statements/test_upload_statement.py`
- test_classes: TestUploadStatement
- test_functions: 0

## `backend/tests/api/routes/test_apply_rules.py`
- test_functions: 16
- names: test_apply_rules_by_transaction_ids_success, test_apply_rules_by_statement_id_success, test_apply_rules_multiple_rules_match, test_apply_rules_multiple_tags_per_rule, test_apply_rules_empty_request_applies_to_all, test_apply_rules_no_matching_rules, test_apply_rules_no_active_rules, test_apply_rules_invalid_transaction_ids, test_apply_rules_idempotent, test_apply_rules_skips_soft_deleted_tags, test_apply_rules_user_isolation_transaction_ids, test_apply_rules_user_isolation_statement_id, test_apply_rules_response_format, test_create_transaction_auto_applies_rules, test_create_transaction_succeeds_when_no_rules, test_create_transaction_succeeds_when_rule_fails

## `backend/tests/api/routes/test_credit_cards.py`
- test_functions: 8
- names: test_update_credit_limit_success, test_update_credit_limit_validation, test_update_credit_limit_metadata_refresh, test_update_other_fields_leaves_limit_metadata_unchanged, test_update_credit_limit_null_does_not_set_manual_source, test_update_credit_card_not_found, test_get_card_outstanding_balance, test_list_cards_outstanding_balance

## `backend/tests/api/routes/test_currency_convert.py`
- test_classes: TestCurrencyConvert
- test_functions: 0

## `backend/tests/api/routes/test_currency_extract.py`
- test_classes: TestCurrencyExtract, TestExtractionJob
- test_functions: 0

## `backend/tests/api/routes/test_currency_rates.py`
- test_classes: TestCurrencyRates
- test_functions: 0

## `backend/tests/api/routes/test_list_transactions.py`
- test_classes: TestListTransactionsOwnership
- test_functions: 0

## `backend/tests/api/routes/test_login.py`
- test_functions: 7
- names: test_get_access_token, test_get_access_token_incorrect_password, test_use_access_token, test_recovery_password, test_recovery_password_user_not_exits, test_reset_password, test_reset_password_invalid_token

## `backend/tests/api/routes/test_private.py`
- test_functions: 1
- names: test_create_user

## `backend/tests/api/routes/test_rules.py`
- test_functions: 13
- names: test_create_rule_success, test_create_rule_missing_conditions_400, test_create_rule_missing_actions_400, test_create_rule_invalid_tag_400, test_list_rules_pagination, test_list_rules_user_isolation, test_get_rule_success, test_get_rule_not_found_404, test_create_rule_invalid_operator_for_field_400, test_create_rule_between_without_value_secondary_400, test_update_rule_success, test_delete_rule_success, test_delete_rule_not_found_404

## `backend/tests/api/routes/test_transaction_tags.py`
- test_classes: TestGetTransactionTagsOwnership
- test_functions: 0

## `backend/tests/api/routes/test_upload_jobs.py`
- test_classes: TestGetUploadJob
- test_functions: 0

## `backend/tests/api/routes/test_users.py`
- test_functions: 27
- names: test_get_users_superuser_me, test_get_users_normal_user_me, test_create_user_new_email, test_get_existing_user, test_get_existing_user_current_user, test_get_existing_user_permissions_error, test_create_user_existing_username, test_create_user_by_normal_user, test_retrieve_users, test_update_user_me, test_update_user_me_preferred_currency, test_update_user_me_clear_preferred_currency, test_update_password_me, test_update_password_me_incorrect_password, test_update_user_me_email_exists, test_update_password_me_same_password_error, test_register_user, test_register_user_already_exists_error, test_update_user, test_update_user_not_exists, test_update_user_email_exists, test_delete_user_me, test_delete_user_me_as_superuser, test_delete_user_super_user, test_delete_user_not_found, test_delete_user_current_super_user_error, test_delete_user_without_privileges

## `backend/tests/api/test_currency.py`
- test_classes: TestCurrencyIntegration
- test_functions: 0

## `backend/tests/conftest.py`
- test_functions: 0

## `backend/tests/crud/__init__.py`
- test_functions: 0

## `backend/tests/crud/rules/__init__.py`
- test_functions: 0

## `backend/tests/crud/rules/test_rule_evaluation_service.py`
- test_classes: TestContainsOperator, TestEqualsOperator, TestNumericOperators, TestDateOperators, TestRuleEvaluation, TestEdgeCases, TestZeroAndNegativeAmounts, TestEmptyStringEdgeCases
- test_functions: 0

## `backend/tests/crud/rules/test_rule_service.py`
- test_classes: TestCreateRule, TestGetRule, TestListRules, TestUpdateRule, TestDeleteRule, TestOperatorValidation
- test_functions: 0

## `backend/tests/crud/test_tag.py`
- test_functions: 7
- names: test_delete_tag_sets_deleted_at_timestamp, test_list_excludes_deleted_tags, test_get_by_id_excludes_deleted_tags_by_default, test_get_by_id_with_include_deleted_returns_deleted_tags, test_count_excludes_deleted_tags, test_delete_already_deleted_tag_raises_error, test_update_deleted_tag_raises_error

## `backend/tests/crud/test_user.py`
- test_functions: 9
- names: test_create_user, test_authenticate_user, test_not_authenticate_user, test_check_if_user_is_active, test_check_if_user_is_active_inactive, test_check_if_user_is_superuser, test_check_if_user_is_superuser_normal_user, test_get_user, test_update_user

## `backend/tests/domains/credit_cards/__init__.py`
- test_functions: 0

## `backend/tests/domains/credit_cards/test_credit_card_models.py`
- test_classes: TestLimitSource, TestCreditCardLimitFields, TestCreditCardDefaultCurrency, TestCreditCardAlias
- test_functions: 0

## `backend/tests/domains/credit_cards/test_credit_card_repository.py`
- test_classes: TestCreditCardRepositoryOutstandingBalance
- test_functions: 0

## `backend/tests/domains/currency/test_exchange_rate_extractor.py`
- test_classes: TestExtractedRate, TestExchangeRateExtractor
- test_functions: 0

## `backend/tests/domains/currency/test_exchange_rate_model.py`
- test_classes: TestExchangeRateModel
- test_functions: 0

## `backend/tests/domains/currency/test_exchange_rate_repository.py`
- test_classes: TestExchangeRateRepositoryGetRateForDate, TestExchangeRateRepositoryGetClosestRate, TestExchangeRateRepositoryGetLatestRate, TestExchangeRateRepositoryGetRatesInRange, TestExchangeRateRepositoryUpsertRate
- test_functions: 0

## `backend/tests/domains/currency/test_rate_scheduler.py`
- test_classes: TestRateExtractionScheduler
- test_functions: 0

## `backend/tests/domains/upload_jobs/usecases/__init__.py`
- test_functions: 0

## `backend/tests/domains/upload_jobs/usecases/test_process_upload.py`
- test_classes: TestSanitizedErrorMessages, TestAtomicImport, TestCreditLimitUpdate, TestProcessUploadJob, TestApplyRules
- test_functions: 0

## `backend/tests/e2e/__init__.py`
- test_functions: 0

## `backend/tests/e2e/test_upload_workflow.py`
- test_classes: TestUploadWorkflowE2E, TestJobStatusE2E, TestFullUploadFlow
- test_functions: 0

## `backend/tests/integration/test_credit_limits_flow.py`
- test_classes: TestCreditLimitsFlow
- test_functions: 0

## `backend/tests/models/__init__.py`
- test_functions: 0

## `backend/tests/models/test_card_statement_models.py`
- test_classes: TestStatementStatusEnum, TestCardStatementCurrency, TestCardStatementStatus, TestCardStatementSourceFilePath, TestCardStatementCreate, TestCardStatementUpdate, TestCardStatementTableModel
- test_functions: 0

## `backend/tests/models/test_upload_job_models.py`
- test_classes: TestUploadJobStatusEnum, TestUploadJobDefaults, TestUploadJobCreate, TestUploadJobPublic, TestUploadJobErrors, TestUploadJobTableModel
- test_functions: 0

## `backend/tests/pkgs/currency/__init__.py`
- test_functions: 0

## `backend/tests/pkgs/currency/test_client.py`
- test_classes: TestExchangeRateClient
- test_functions: 0

## `backend/tests/pkgs/currency/test_service.py`
- test_classes: TestCurrencyService, TestProvide
- test_functions: 0

## `backend/tests/pkgs/extraction/__init__.py`
- test_functions: 0

## `backend/tests/pkgs/extraction/test_client.py`
- test_classes: TestOpenRouterClient
- test_functions: 0

## `backend/tests/pkgs/extraction/test_models.py`
- test_classes: TestMoney, TestInstallmentInfo, TestExtractedTransaction, TestExtractedCycle, TestExtractedCard, TestExtractedStatement, TestExtractionResult
- test_functions: 0

## `backend/tests/pkgs/extraction/test_service.py`
- test_classes: TestExtractionService, TestProvideFunction
- test_functions: 0

## `backend/tests/pkgs/storage/test_storage.py`
- test_classes: TestStorageClient, TestStorageService, TestProvideFunction
- test_functions: 0

## `backend/tests/repositories/__init__.py`
- test_functions: 0

## `backend/tests/repositories/test_upload_job_repository.py`
- test_classes: TestUploadJobRepositoryCreate, TestUploadJobRepositoryGetById, TestUploadJobRepositoryGetByFileHash, TestUploadJobRepositoryUpdateStatus
- test_functions: 0

## `backend/tests/scripts/__init__.py`
- test_functions: 0

## `backend/tests/scripts/test_backend_pre_start.py`
- test_functions: 1
- names: test_init_successful_connection

## `backend/tests/scripts/test_test_pre_start.py`
- test_functions: 1
- names: test_init_successful_connection

## `backend/tests/services/test_upload_job_service.py`
- test_classes: TestUploadJobServiceCreate, TestUploadJobServiceGet, TestUploadJobServiceUpdateStatus, TestUploadJobServiceIncrementRetry
- test_functions: 0

## `backend/tests/test_lifespan.py`
- test_functions: 1
- names: test_lifespan_scheduler_start_stop

## `backend/tests/utils/__init__.py`
- test_functions: 0

## `backend/tests/utils/user.py`
- test_functions: 0

## `backend/tests/utils/utils.py`
- test_functions: 0
