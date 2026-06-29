{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold']
) }}

WITH events AS (
    SELECT DISTINCT
        event_id,
        event_name,
        venue
    FROM {{ ref('fact_tickets') }}
    WHERE event_id IS NOT NULL
)

SELECT
    ROW_NUMBER() OVER (ORDER BY event_id) AS event_key,
    event_id,
    event_name,
    venue,
    CURRENT_TIMESTAMP() AS created_at
FROM events
