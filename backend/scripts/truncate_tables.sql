-- =============================================================================
-- Truncate Tables Script
-- =============================================================================
-- This script truncates all data from the credit card, statement, transaction,
-- tag, and payment tables.
--
-- WARNING: This will delete ALL data in these tables for ALL users.
-- Use with caution.
--
-- Usage: psql -d <database> -f truncate_tables.sql
-- =============================================================================

BEGIN;

TRUNCATE TABLE
    transaction_tags,
    tags,
    payment,
    transaction,
    card_statement,
    credit_card
CASCADE;

COMMIT;
