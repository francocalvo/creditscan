-- =============================================================================
-- Credit Card Seeding Script
-- =============================================================================
-- This script seeds the database with credit card test data for a given user.
-- Includes 8 credit cards, 16 statements (current + last month), transactions,
-- and payments for last month statements.
--
-- Usage: psql -d <database> -f seed_credit_cards.sql
-- =============================================================================

-- Configuration: Set the user email here
\set user_email 'dev@francocalvo.ar'

-- =============================================================================
-- CLEANUP: Remove existing data for user (optional - comment out to append)
-- =============================================================================

DO $$
DECLARE
    v_user_id UUID;
BEGIN
    SELECT id INTO v_user_id FROM "user" WHERE email = :'user_email';

    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'User with email % not found', :'user_email';
    END IF;

    -- Delete payments for this user
    DELETE FROM payment WHERE user_id = v_user_id;

    -- Delete transactions for this user's statements
    DELETE FROM transaction
    WHERE statement_id IN (
        SELECT cs.id FROM card_statement cs
        JOIN credit_card cc ON cs.card_id = cc.id
        WHERE cc.user_id = v_user_id
    );

    -- Delete statements for this user's cards
    DELETE FROM card_statement
    WHERE card_id IN (
        SELECT id FROM credit_card WHERE user_id = v_user_id
    );

    -- Delete credit cards for this user
    DELETE FROM credit_card WHERE user_id = v_user_id;

    RAISE NOTICE 'Cleaned up existing data for user %', :'user_email';
END $$;

-- =============================================================================
-- INSERT CREDIT CARDS (8 total)
-- =============================================================================

WITH user_data AS (
    SELECT id AS user_id FROM "user" WHERE email = :'user_email'
),
card_data AS (
    SELECT
        gen_random_uuid() AS id,
        user_id,
        bank,
        brand::cardbrand,
        last4
    FROM user_data,
    (VALUES
        ('ICBC', 'MASTERCARD', '4521'),
        ('ICBC', 'VISA', '7832'),
        ('Santander', 'VISA', '3456'),
        ('Santander', 'AMEX', '9012'),
        ('BBVA', 'MASTERCARD', '6789'),
        ('BBVA', 'VISA', '2345'),
        ('MercadoPago', 'MASTERCARD', '8901'),
        ('Galicia', 'VISA', '5678')
    ) AS cards(bank, brand, last4)
)
INSERT INTO credit_card (id, user_id, bank, brand, last4)
SELECT id, user_id, bank, brand, last4 FROM card_data;

-- =============================================================================
-- INSERT STATEMENTS (16 total: 8 current month + 8 last month)
-- =============================================================================

WITH user_data AS (
    SELECT id AS user_id FROM "user" WHERE email = :'user_email'
),
cards AS (
    SELECT cc.id AS card_id, cc.bank, cc.brand
    FROM credit_card cc
    JOIN user_data u ON cc.user_id = u.user_id
),
statement_data AS (
    -- Current month statements (not paid)
    SELECT
        gen_random_uuid() AS id,
        card_id,
        date_trunc('month', CURRENT_DATE)::date AS period_start,
        (date_trunc('month', CURRENT_DATE) + interval '1 month' - interval '1 day')::date AS period_end,
        (date_trunc('month', CURRENT_DATE) + interval '1 month' + interval '5 days')::date AS close_date,
        (date_trunc('month', CURRENT_DATE) + interval '1 month' + interval '15 days')::date AS due_date,
        0.00 AS previous_balance,
        0.00 AS current_balance,
        0.00 AS minimum_payment,
        false AS is_fully_paid,
        'current' AS month_type
    FROM cards

    UNION ALL

    -- Last month statements (paid)
    SELECT
        gen_random_uuid() AS id,
        card_id,
        (date_trunc('month', CURRENT_DATE) - interval '1 month')::date AS period_start,
        (date_trunc('month', CURRENT_DATE) - interval '1 day')::date AS period_end,
        (date_trunc('month', CURRENT_DATE) + interval '5 days')::date AS close_date,
        (date_trunc('month', CURRENT_DATE) + interval '15 days')::date AS due_date,
        0.00 AS previous_balance,
        0.00 AS current_balance,
        0.00 AS minimum_payment,
        true AS is_fully_paid,
        'last' AS month_type
    FROM cards
)
INSERT INTO card_statement (id, card_id, period_start, period_end, close_date, due_date, previous_balance, current_balance, minimum_payment, is_fully_paid)
SELECT id, card_id, period_start, period_end, close_date, due_date, previous_balance, current_balance, minimum_payment, is_fully_paid
FROM statement_data;

-- =============================================================================
-- INSERT TRANSACTIONS (random 0-35 per statement)
-- =============================================================================

WITH user_data AS (
    SELECT id AS user_id FROM "user" WHERE email = :'user_email'
),
statements AS (
    SELECT
        cs.id AS statement_id,
        cs.period_start,
        cs.period_end,
        cs.is_fully_paid,
        -- Random transaction count between 0-35
        floor(random() * 36)::int AS txn_count
    FROM card_statement cs
    JOIN credit_card cc ON cs.card_id = cc.id
    JOIN user_data u ON cc.user_id = u.user_id
),
payees AS (
    SELECT unnest(ARRAY[
        -- Supermarkets
        'Carrefour', 'Coto', 'Jumbo', 'Disco', 'La Anonima', 'Dia', 'Changomas',
        -- Fast food
        'McDonalds', 'Burger King', 'Mostaza', 'Wendys', 'KFC',
        -- Restaurants
        'La Cabrera', 'Don Julio', 'Sushi Pop', 'Kansas', 'Cabaña Las Lilas',
        -- Streaming
        'Netflix', 'Spotify', 'Disney+', 'HBO Max', 'Amazon Prime', 'YouTube Premium',
        -- Gas stations
        'YPF', 'Shell', 'Axion', 'Puma Energy',
        -- Health
        'Farmacity', 'Farmacia del Pueblo', 'OSDE', 'Swiss Medical', 'Galeno',
        -- E-commerce
        'MercadoLibre', 'Amazon', 'Tienda Nube', 'Garbarino', 'Fravega',
        -- Services
        'Edenor', 'Metrogas', 'Telecom', 'Personal', 'Movistar', 'Claro',
        -- Entertainment
        'Cinemark', 'Hoyts', 'Ticketek', 'AllAccess',
        -- Travel
        'Despegar', 'Aerolineas Argentinas', 'LATAM', 'Booking.com',
        -- Others
        'Starbucks', 'Cafe Martinez', 'Havanna', 'Rappi', 'PedidosYa'
    ]) AS payee
),
payee_numbered AS (
    SELECT payee, row_number() OVER () AS payee_num, count(*) OVER () AS total_payees
    FROM payees
),
transactions_expanded AS (
    SELECT
        s.statement_id,
        s.period_start,
        s.period_end,
        generate_series(1, GREATEST(s.txn_count, 0)) AS txn_num,
        s.txn_count
    FROM statements s
    WHERE s.txn_count > 0
)
INSERT INTO transaction (id, statement_id, txn_date, payee, description, amount, currency, coupon, installment_cur, installment_tot)
SELECT
    gen_random_uuid() AS id,
    te.statement_id,
    -- Random date within the statement period
    (te.period_start + (random() * (te.period_end - te.period_start))::int)::date AS txn_date,
    pn.payee,
    -- Description based on payee
    CASE
        WHEN pn.payee IN ('Netflix', 'Spotify', 'Disney+', 'HBO Max', 'Amazon Prime', 'YouTube Premium')
            THEN 'Suscripcion mensual'
        WHEN pn.payee IN ('Carrefour', 'Coto', 'Jumbo', 'Disco', 'La Anonima', 'Dia', 'Changomas')
            THEN 'Compras supermercado'
        WHEN pn.payee IN ('YPF', 'Shell', 'Axion', 'Puma Energy')
            THEN 'Carga de combustible'
        WHEN pn.payee IN ('Edenor', 'Metrogas', 'Telecom', 'Personal', 'Movistar', 'Claro')
            THEN 'Pago de servicio'
        WHEN pn.payee IN ('Farmacity', 'Farmacia del Pueblo')
            THEN 'Compra farmacia'
        WHEN pn.payee IN ('OSDE', 'Swiss Medical', 'Galeno')
            THEN 'Cuota prepaga medica'
        WHEN pn.payee IN ('MercadoLibre', 'Amazon', 'Tienda Nube', 'Garbarino', 'Fravega')
            THEN 'Compra online'
        WHEN pn.payee IN ('Cinemark', 'Hoyts')
            THEN 'Entradas cine'
        WHEN pn.payee IN ('Despegar', 'Aerolineas Argentinas', 'LATAM', 'Booking.com')
            THEN 'Reserva viaje'
        ELSE 'Consumo'
    END AS description,
    -- Random amount between 5000 and 150000 ARS
    round((5000 + random() * 145000)::numeric, 2) AS amount,
    'ARS' AS currency,
    NULL AS coupon,
    -- Some transactions have installments (20% chance)
    inst.installment_cur,
    inst.installment_tot
FROM transactions_expanded te
CROSS JOIN LATERAL (
    SELECT payee
    FROM payee_numbered
    ORDER BY random()
    LIMIT 1
) pn
CROSS JOIN LATERAL (
    SELECT
        CASE WHEN r < 0.2
            THEN floor(1 + random() * tot)::int
            ELSE NULL
        END AS installment_cur,
        CASE WHEN r < 0.2
            THEN tot
            ELSE NULL
        END AS installment_tot
    FROM (SELECT random() AS r, floor(3 + random() * 10)::int AS tot) AS rand_vals
) inst;

-- =============================================================================
-- UPDATE STATEMENT BALANCES based on transactions
-- =============================================================================

WITH user_data AS (
    SELECT id AS user_id FROM "user" WHERE email = :'user_email'
),
statement_totals AS (
    SELECT
        cs.id AS statement_id,
        COALESCE(SUM(t.amount), 0) AS total_amount
    FROM card_statement cs
    JOIN credit_card cc ON cs.card_id = cc.id
    JOIN user_data u ON cc.user_id = u.user_id
    LEFT JOIN transaction t ON t.statement_id = cs.id
    GROUP BY cs.id
)
UPDATE card_statement cs
SET
    current_balance = st.total_amount,
    minimum_payment = round(st.total_amount * 0.15, 2)
FROM statement_totals st
WHERE cs.id = st.statement_id;

-- =============================================================================
-- INSERT PAYMENTS for last month statements (full payment)
-- =============================================================================

WITH user_data AS (
    SELECT id AS user_id FROM "user" WHERE email = :'user_email'
),
last_month_statements AS (
    SELECT
        cs.id AS statement_id,
        u.user_id,
        cs.current_balance,
        cs.due_date
    FROM card_statement cs
    JOIN credit_card cc ON cs.card_id = cc.id
    JOIN user_data u ON cc.user_id = u.user_id
    WHERE cs.is_fully_paid = true
      AND cs.current_balance > 0
)
INSERT INTO payment (id, user_id, statement_id, amount, payment_date, currency)
SELECT
    gen_random_uuid() AS id,
    user_id,
    statement_id,
    current_balance AS amount,
    -- Payment made a few days before due date
    (due_date - interval '3 days')::date AS payment_date,
    'ARS' AS currency
FROM last_month_statements;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Show created cards
SELECT
    '--- Credit Cards ---' AS section;

SELECT
    bank,
    brand::text,
    last4
FROM credit_card
WHERE user_id = (SELECT id FROM "user" WHERE email = :'user_email')
ORDER BY bank, brand;

-- Show statements summary
SELECT
    '--- Statements Summary ---' AS section;

SELECT
    cc.bank,
    cc.brand::text,
    cs.period_start,
    cs.is_fully_paid,
    cs.current_balance,
    cs.minimum_payment
FROM card_statement cs
JOIN credit_card cc ON cs.card_id = cc.id
WHERE cc.user_id = (SELECT id FROM "user" WHERE email = :'user_email')
ORDER BY cs.period_start DESC, cc.bank;

-- Show transaction counts per card/statement
SELECT
    '--- Transaction Counts ---' AS section;

SELECT
    cc.bank,
    cc.brand::text,
    CASE WHEN cs.is_fully_paid THEN 'Last Month' ELSE 'Current Month' END AS period,
    COUNT(t.id) AS txn_count,
    COALESCE(SUM(t.amount), 0) AS total_amount
FROM card_statement cs
JOIN credit_card cc ON cs.card_id = cc.id
LEFT JOIN transaction t ON t.statement_id = cs.id
WHERE cc.user_id = (SELECT id FROM "user" WHERE email = :'user_email')
GROUP BY cc.bank, cc.brand, cs.is_fully_paid
ORDER BY cc.bank, cc.brand, cs.is_fully_paid;

-- Show payments
SELECT
    '--- Payments ---' AS section;

SELECT
    cc.bank,
    cc.brand::text,
    p.amount,
    p.payment_date
FROM payment p
JOIN card_statement cs ON p.statement_id = cs.id
JOIN credit_card cc ON cs.card_id = cc.id
WHERE p.user_id = (SELECT id FROM "user" WHERE email = :'user_email')
ORDER BY p.payment_date DESC;

SELECT
    '--- Seeding Complete ---' AS section;
