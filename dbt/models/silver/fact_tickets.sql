{{ config(
    materialized='incremental',
    schema='SILVER',
    unique_key='ticket_id',
    tags=['tickets']
) }}

SELECT
    TICKET_DATA:ticket_id::STRING           AS ticket_id,
    TICKET_DATA:event_id::STRING            AS event_id,
    TICKET_DATA:event_name::STRING          AS event_name,
    TICKET_DATA:venue::STRING               AS venue,
    TICKET_DATA:category::STRING            AS category,
    TICKET_DATA:price::NUMBER(10,2)         AS price,
    TICKET_DATA:currency::STRING            AS currency,
    TICKET_DATA:status::STRING              AS ticket_status,
    TICKET_DATA:purchase_timestamp::TIMESTAMP_NTZ AS purchase_timestamp,
    TICKET_DATA:attendee_email_hash::STRING AS attendee_email_hash,
    BATCH_ID,
    LOADED_AT
FROM {{ source('bronze', 'raw_tickets') }}
WHERE TICKET_DATA:ticket_id IS NOT NULL

{% if is_incremental() %}
  AND LOADED_AT > (SELECT MAX(LOADED_AT) FROM {{ this }})
{% endif %}

QUALIFY ROW_NUMBER() OVER (PARTITION BY TICKET_DATA:ticket_id::STRING ORDER BY LOADED_AT DESC) = 1
