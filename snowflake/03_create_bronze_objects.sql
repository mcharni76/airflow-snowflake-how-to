------------------------------------------------------------
-- Events Pipeline: Bronze Landing Table
-- Step 3: Raw tickets landing zone (VARIANT-based)
-- Run with EVENTS_DEV_ROLE
------------------------------------------------------------

USE ROLE EVENTS_DEV_ROLE;
USE DATABASE EVENTS_DEV;
USE SCHEMA BRONZE;
USE WAREHOUSE COMPUTE_WH;

CREATE TABLE IF NOT EXISTS EVENTS_DEV.BRONZE.RAW_TICKETS (
  BATCH_ID        STRING        NOT NULL,
  TICKET_DATA     VARIANT       NOT NULL,
  SOURCE_FILE     STRING,
  LOADED_AT       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
