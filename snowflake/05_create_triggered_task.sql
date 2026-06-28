------------------------------------------------------------
-- Events Pipeline: Triggered Task for Bronze Landing (MERGE)
-- Step 5: Deduplicating Bronze load via MERGE on ticket_id
-- Run with EVENTS_DEV_ROLE
------------------------------------------------------------

USE ROLE EVENTS_DEV_ROLE;
USE DATABASE EVENTS_DEV;
USE SCHEMA RAW;
USE WAREHOUSE COMPUTE_WH;

CREATE FILE FORMAT IF NOT EXISTS EVENTS_DEV.RAW.JSON_FORMAT
  TYPE = 'JSON'
  STRIP_OUTER_ARRAY = FALSE
  COMPRESSION = 'NONE';

CREATE OR REPLACE TASK EVENTS_DEV.RAW.LAND_TICKETS_BRONZE
  WAREHOUSE = COMPUTE_WH
  WHEN SYSTEM$STREAM_HAS_DATA('EVENTS_DEV.RAW.TICKETING_STAGE_STREAM')
AS
BEGIN
  LET c1 CURSOR FOR
    SELECT RELATIVE_PATH
    FROM EVENTS_DEV.RAW.TICKETING_STAGE_STREAM
    WHERE METADATA$ACTION = 'INSERT';

  FOR rec IN c1 DO
    LET v_file_path STRING := rec.RELATIVE_PATH;
    LET v_batch_id STRING := SPLIT_PART(SPLIT_PART(:v_file_path, 'batch_id=', 2), '/', 1);
    LET v_stage_full STRING := '@EVENTS_DEV.RAW.TICKETING_STAGE/' || :v_file_path;

    LET v_sql STRING := '
      MERGE INTO EVENTS_DEV.BRONZE.RAW_TICKETS tgt
      USING (
        SELECT
          ''' || :v_batch_id || ''' AS batch_id,
          t.VALUE AS ticket_data,
          t.VALUE:ticket_id::STRING AS ticket_id,
          ''' || :v_file_path || ''' AS source_file
        FROM ' || :v_stage_full || ' (FILE_FORMAT => ''EVENTS_DEV.RAW.JSON_FORMAT'') AS s,
        LATERAL FLATTEN(input => s.$1:data) t
      ) src
      ON tgt.TICKET_DATA:ticket_id::STRING = src.ticket_id
      WHEN NOT MATCHED THEN INSERT (BATCH_ID, TICKET_DATA, SOURCE_FILE)
        VALUES (src.batch_id, src.ticket_data, src.source_file)';

    EXECUTE IMMEDIATE :v_sql;

    LET v_count NUMBER := (SELECT COUNT(*) FROM EVENTS_DEV.BRONZE.RAW_TICKETS WHERE BATCH_ID = :v_batch_id);
    CALL EVENTS_DEV.ORCH.UPDATE_BATCH_STATUS(:v_batch_id, 'BRONZE_COMPLETE', :v_count, NULL);
  END FOR;
END;

ALTER TASK EVENTS_DEV.RAW.LAND_TICKETS_BRONZE RESUME;
