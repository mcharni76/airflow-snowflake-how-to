------------------------------------------------------------
-- Events Pipeline: Internal Stage and Directory Stream
-- Step 2: Named internal stage with directory table + stream
-- Run with EVENTS_DEV_ROLE
------------------------------------------------------------

USE ROLE EVENTS_DEV_ROLE;
USE DATABASE EVENTS_DEV;
USE SCHEMA RAW;
USE WAREHOUSE COMPUTE_WH;

CREATE STAGE IF NOT EXISTS EVENTS_DEV.RAW.TICKETING_STAGE
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

CREATE STREAM IF NOT EXISTS EVENTS_DEV.RAW.TICKETING_STAGE_STREAM
  ON STAGE EVENTS_DEV.RAW.TICKETING_STAGE;
