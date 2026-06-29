{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold']
) }}

SELECT
    purchase_timestamp::DATE AS revenue_date,
    event_id,
    event_name,
    category,
    COUNT(*) AS total_tickets,
    SUM(price) AS total_revenue,
    ROUND(AVG(price), 2) AS avg_ticket_price
FROM {{ ref('fact_tickets') }}
WHERE ticket_status NOT IN ('cancelled', 'refunded')
GROUP BY
    purchase_timestamp::DATE,
    event_id,
    event_name,
    category
