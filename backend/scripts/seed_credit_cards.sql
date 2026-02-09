-- =============================================================================
-- Credit Card Seeding Script
-- =============================================================================
-- This script seeds the database with credit card test data for a given user.
-- Includes 8 credit cards, 16 statements (current + last month), transactions,
-- payments, and tags.
--
-- Usage: psql -d <database> -f seed_credit_cards.sql
-- =============================================================================

-- Configuration: Pass user_email via -v flag, e.g.:
--   psql -v user_email="'dev@francocalvo.ar'" -f seed_credit_cards.sql

-- =============================================================================
-- CLEANUP: Remove existing data for user (optional - comment out to append)
-- =============================================================================

-- Delete transaction tags for this user's tags
DELETE FROM transaction_tags
WHERE tag_id IN (
    SELECT tag_id FROM tags 
    WHERE user_id = (SELECT id FROM "user" WHERE email = :'user_email')
);

-- Delete tags for this user
DELETE FROM tags 
WHERE user_id = (SELECT id FROM "user" WHERE email = :'user_email');

-- Delete payments for this user
DELETE FROM payment 
WHERE user_id = (SELECT id FROM "user" WHERE email = :'user_email');

-- Delete transactions for this user's statements
DELETE FROM transaction
WHERE statement_id IN (
    SELECT cs.id FROM card_statement cs
    JOIN credit_card cc ON cs.card_id = cc.id
    WHERE cc.user_id = (SELECT id FROM "user" WHERE email = :'user_email')
);

-- Delete statements for this user's cards
DELETE FROM card_statement
WHERE card_id IN (
    SELECT id FROM credit_card 
    WHERE user_id = (SELECT id FROM "user" WHERE email = :'user_email')
);

-- Delete credit cards for this user
DELETE FROM credit_card 
WHERE user_id = (SELECT id FROM "user" WHERE email = :'user_email');

-- =============================================================================
-- INSERT TAGS (8 total)
-- =============================================================================

WITH user_data AS (
    SELECT id AS user_id FROM "user" WHERE email = :'user_email'
),
tag_names AS (
    SELECT unnest(ARRAY[
        'Alimentacion',
        'Transporte',
        'Servicios',
        'Entretenimiento',
        'Salud',
        'Compras',
        'Viajes',
        'Ropa'
    ]) AS label
)
INSERT INTO tags (tag_id, user_id, label, created_at)
SELECT gen_random_uuid(), user_id, label, NOW() FROM user_data, tag_names;

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
        last4,
        credit_limit::numeric(32,2) AS credit_limit,
        'ARS' AS default_currency
    FROM user_data,
    (VALUES
        ('ICBC', 'MASTERCARD', '4521', 1800000),
        ('ICBC', 'VISA', '7832', 1250000),
        ('Santander', 'VISA', '3456', 1500000),
        ('Santander', 'AMEX', '9012', 2200000),
        ('BBVA', 'MASTERCARD', '6789', 1100000),
        ('BBVA', 'VISA', '2345', 950000),
        ('MercadoPago', 'MASTERCARD', '8901', 700000),
        ('Galicia', 'VISA', '5678', 1300000)
    ) AS cards(bank, brand, last4, credit_limit)
)
INSERT INTO credit_card (
    id,
    user_id,
    bank,
    brand,
    last4,
    default_currency,
    credit_limit,
    limit_source,
    limit_last_updated_at
)
SELECT
    id,
    user_id,
    bank,
    brand,
    last4,
    default_currency,
    credit_limit,
    'manual',
    NOW()
FROM card_data;

-- =============================================================================
-- INSERT STATEMENTS (48 total: 8 cards * 6 months)
-- =============================================================================

WITH user_data AS (
    SELECT id AS user_id FROM "user" WHERE email = :'user_email'
),
cards AS (
    SELECT cc.id AS card_id, cc.bank, cc.brand,
           row_number() OVER (ORDER BY cc.bank, cc.brand) AS card_num
    FROM credit_card cc
    JOIN user_data u ON cc.user_id = u.user_id
),
months AS (
    -- Generate offsets for current month (0) and 5 previous months (1-5)
    SELECT generate_series(0, 5) AS m_offset
),
statement_data AS (
    SELECT
        gen_random_uuid() AS id,
        c.card_id,
        -- Period Start: 1st of the calculated month
        (date_trunc('month', CURRENT_DATE) - (m.m_offset || ' month')::interval)::date AS period_start,
        -- Period End: Last day of that month
        ((date_trunc('month', CURRENT_DATE) - (m.m_offset || ' month')::interval) + interval '1 month' - interval '1 day')::date AS period_end,
        -- Close Date: 5th of next month
        ((date_trunc('month', CURRENT_DATE) - (m.m_offset || ' month')::interval) + interval '1 month' + interval '5 days')::date AS close_date,
        -- Due Date: 15th of next month
        ((date_trunc('month', CURRENT_DATE) - (m.m_offset || ' month')::interval) + interval '1 month' + interval '15 days')::date AS due_date,
        0.00 AS previous_balance,
        0.00 AS current_balance,
        0.00 AS minimum_payment,
        -- Current month (offset 0) is not paid, past months are fully paid
        CASE WHEN m.m_offset = 0 THEN false ELSE true END AS is_fully_paid,
        'ARS' AS currency,
        -- Santander AMEX current month statement is PENDING_REVIEW, rest are COMPLETE
        CASE WHEN m.m_offset = 0 AND c.bank = 'Santander' AND c.brand::text = 'AMEX' THEN 'PENDING_REVIEW'::statementstatus ELSE 'COMPLETE'::statementstatus END AS status,
        CASE WHEN m.m_offset = 0 THEN 'current' ELSE 'past' END AS month_type
    FROM cards c
    CROSS JOIN months m
)
INSERT INTO card_statement (id, card_id, period_start, period_end, close_date, due_date, previous_balance, current_balance, minimum_payment, is_fully_paid, currency, status)
SELECT id, card_id, period_start, period_end, close_date, due_date, previous_balance, current_balance, minimum_payment, is_fully_paid, currency, status
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
        'Carrefour', 'Coto', 'Jumbo', 'Disco', 'La Anonima', 'Dia', 'Changomas', 'Vea', 'Makro',
        -- Fast food
        'McDonalds', 'Burger King', 'Mostaza', 'Wendys', 'KFC', 'Subway', 'Dean & Dennys',
        -- Restaurants
        'La Cabrera', 'Don Julio', 'Sushi Pop', 'Kansas', 'Cabaña Las Lilas', 'El Club de la Milanesa', 'Kentucky',
        -- Streaming / Gaming
        'Netflix', 'Spotify', 'Disney+', 'HBO Max', 'Amazon Prime', 'YouTube Premium', 'Steam', 'PlayStation', 'Xbox',
        -- Gas stations
        'YPF', 'Shell', 'Axion', 'Puma Energy',
        -- Health
        'Farmacity', 'Farmacia del Pueblo', 'OSDE', 'Swiss Medical', 'Galeno', 'Dr Ahorro',
        -- E-commerce
        'MercadoLibre', 'Amazon', 'Tienda Nube', 'Garbarino', 'Fravega', 'Musimundo',
        -- Services
        'Edenor', 'Metrogas', 'Telecom', 'Personal', 'Movistar', 'Claro', 'AySA', 'ABL',
        -- Entertainment
        'Cinemark', 'Hoyts', 'Ticketek', 'AllAccess', 'Teatro Colon',
        -- Travel / Transport
        'Despegar', 'Aerolineas Argentinas', 'LATAM', 'Booking.com', 'Uber', 'Cabify', 'DiDi', 'Flybondi',
        -- Clothing
        'Zara', 'H&M', 'Adidas', 'Nike', 'Puma', 'Lacoste',
        -- Others
        'Starbucks', 'Cafe Martinez', 'Havanna', 'Rappi', 'PedidosYa', 'Gym Pass', 'Megatlon'
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
    -- Description based on payee with more variety
    CASE
        WHEN pn.payee IN ('Netflix', 'Spotify', 'Disney+', 'HBO Max', 'Amazon Prime', 'YouTube Premium', 'Steam', 'PlayStation', 'Xbox')
            THEN (ARRAY['Suscripcion mensual', 'Pago mensual', 'Servicio digital', 'Renovacion auto'])[floor(random()*4+1)]
        WHEN pn.payee IN ('Carrefour', 'Coto', 'Jumbo', 'Disco', 'La Anonima', 'Dia', 'Changomas', 'Vea', 'Makro')
            THEN (ARRAY['Compra presencial', 'Compra online', 'Supermercado', 'Alimentos'])[floor(random()*4+1)]
        WHEN pn.payee IN ('YPF', 'Shell', 'Axion', 'Puma Energy')
            THEN (ARRAY['Carga de combustible', 'Nafta Super', 'Nafta Premium', 'Tienda'])[floor(random()*4+1)]
        WHEN pn.payee IN ('Edenor', 'Metrogas', 'Telecom', 'Personal', 'Movistar', 'Claro', 'AySA', 'ABL')
            THEN (ARRAY['Pago de servicio', 'Factura mensual', 'Vencimiento', 'Pago total'])[floor(random()*4+1)]
        WHEN pn.payee IN ('Farmacity', 'Farmacia del Pueblo', 'Dr Ahorro')
            THEN (ARRAY['Compra farmacia', 'Medicamentos', 'Perfumeria'])[floor(random()*3+1)]
        WHEN pn.payee IN ('OSDE', 'Swiss Medical', 'Galeno')
            THEN 'Cuota prepaga medica'
        WHEN pn.payee IN ('MercadoLibre', 'Amazon', 'Tienda Nube', 'Garbarino', 'Fravega', 'Musimundo')
            THEN (ARRAY['Compra online', 'Electrodomesticos', 'Tecnologia', 'Hogar'])[floor(random()*4+1)]
        WHEN pn.payee IN ('Cinemark', 'Hoyts', 'Ticketek', 'AllAccess', 'Teatro Colon')
            THEN (ARRAY['Entradas', 'Cine 2D', 'Cine 3D', 'Espectaculo', 'Concierto'])[floor(random()*5+1)]
        WHEN pn.payee IN ('Despegar', 'Aerolineas Argentinas', 'LATAM', 'Booking.com', 'Flybondi')
            THEN (ARRAY['Pasajes aereos', 'Reserva hotel', 'Paquete turistico'])[floor(random()*3+1)]
        WHEN pn.payee IN ('Uber', 'Cabify', 'DiDi')
            THEN (ARRAY['Viaje', 'Transporte', 'Traslado'])[floor(random()*3+1)]
        WHEN pn.payee IN ('Zara', 'H&M', 'Adidas', 'Nike', 'Puma', 'Lacoste')
            THEN (ARRAY['Indumentaria', 'Ropa', 'Zapatillas', 'Accesorios'])[floor(random()*4+1)]
        WHEN pn.payee IN ('McDonalds', 'Burger King', 'Mostaza', 'Wendys', 'KFC', 'Subway', 'Dean & Dennys')
            THEN (ARRAY['Almuerzo', 'Cena', 'Combo', 'Fast Food'])[floor(random()*4+1)]
        WHEN pn.payee IN ('La Cabrera', 'Don Julio', 'Sushi Pop', 'Kansas', 'Cabaña Las Lilas', 'El Club de la Milanesa', 'Kentucky')
            THEN (ARRAY['Cena', 'Almuerzo', 'Restaurante', 'Salida'])[floor(random()*4+1)]
        ELSE (ARRAY['Consumo', 'Compra', 'Pago', 'Gasto'])[floor(random()*4+1)]
    END AS description,
    -- Random amount between 2000 and 250000 ARS
    round((2000 + random() * 248000)::numeric, 2) AS amount,
    'ARS' AS currency,
    NULL AS coupon,
    -- Some transactions have installments (20% chance)
    inst.installment_cur,
    inst.installment_tot
FROM transactions_expanded te
CROSS JOIN LATERAL (
    SELECT payee
    FROM payee_numbered
    -- Adding a dummy join condition on te.txn_num forces Postgres to re-evaluate this for each row
    WHERE te.txn_num IS NOT NULL
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
    -- Adding te.txn_num to the subquery to ensure it's re-evaluated for each row
    FROM (SELECT random() AS r, floor(3 + random() * 10)::int AS tot, te.txn_num) AS rand_vals
) inst;

-- =============================================================================
-- INSERT TRANSACTION TAGS
-- =============================================================================

WITH user_tags AS (
    SELECT tag_id, label
    FROM tags
    WHERE user_id = (SELECT id FROM "user" WHERE email = :'user_email')
),
transactions_to_tag AS (
    SELECT t.id AS transaction_id, t.payee
    FROM transaction t
    JOIN card_statement cs ON t.statement_id = cs.id
    JOIN credit_card cc ON cs.card_id = cc.id
    WHERE cc.user_id = (SELECT id FROM "user" WHERE email = :'user_email')
)
INSERT INTO transaction_tags (transaction_id, tag_id)
SELECT
    tt.transaction_id,
    ut.tag_id
FROM transactions_to_tag tt
JOIN user_tags ut ON
    -- Logic to match payees to tags
    (ut.label = 'Alimentacion' AND tt.payee IN ('Carrefour', 'Coto', 'Jumbo', 'Disco', 'La Anonima', 'Dia', 'Changomas', 'Vea', 'Makro', 'McDonalds', 'Burger King', 'Mostaza', 'Wendys', 'KFC', 'Subway', 'Dean & Dennys', 'La Cabrera', 'Don Julio', 'Sushi Pop', 'Kansas', 'Cabaña Las Lilas', 'El Club de la Milanesa', 'Kentucky', 'Starbucks', 'Cafe Martinez', 'Havanna', 'Rappi', 'PedidosYa'))
    OR
    (ut.label = 'Transporte' AND tt.payee IN ('YPF', 'Shell', 'Axion', 'Puma Energy', 'Uber', 'Cabify', 'DiDi', 'Flybondi'))
    OR
    (ut.label = 'Servicios' AND tt.payee IN ('Edenor', 'Metrogas', 'Telecom', 'Personal', 'Movistar', 'Claro', 'AySA', 'ABL', 'OSDE', 'Swiss Medical', 'Galeno'))
    OR
    (ut.label = 'Entretenimiento' AND tt.payee IN ('Netflix', 'Spotify', 'Disney+', 'HBO Max', 'Amazon Prime', 'YouTube Premium', 'Steam', 'PlayStation', 'Xbox', 'Cinemark', 'Hoyts', 'Ticketek', 'AllAccess', 'Teatro Colon'))
    OR
    (ut.label = 'Salud' AND tt.payee IN ('Farmacity', 'Farmacia del Pueblo', 'Dr Ahorro', 'Gym Pass', 'Megatlon'))
    OR
    (ut.label = 'Compras' AND tt.payee IN ('MercadoLibre', 'Amazon', 'Tienda Nube', 'Garbarino', 'Fravega', 'Musimundo'))
    OR
    (ut.label = 'Viajes' AND tt.payee IN ('Despegar', 'Aerolineas Argentinas', 'LATAM', 'Booking.com'))
    OR
    (ut.label = 'Ropa' AND tt.payee IN ('Zara', 'H&M', 'Adidas', 'Nike', 'Puma', 'Lacoste'));

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
-- INSERT PAYMENTS for past statements (full payment)
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
    cs.status,
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

-- Show tags
SELECT
    '--- Tags ---' AS section;

SELECT
    t.label,
    COUNT(tt.transaction_id) as assigned_count
FROM tags t
LEFT JOIN transaction_tags tt ON t.tag_id = tt.tag_id
WHERE t.user_id = (SELECT id FROM "user" WHERE email = :'user_email')
GROUP BY t.label
ORDER BY t.label;

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
