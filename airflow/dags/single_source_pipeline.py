"""
EventHub Ticketing Pipeline — Single-Source Incremental CDC
============================================================

Design principles:
1. Airflow is the CONTROL PLANE. Snowflake is the RUNTIME.
2. Watermark stored in Snowflake (not XCom) — single source of truth.
3. PUT file to internal stage → Stream detects → Triggered task fires → MERGE INTO Bronze.
4. Reschedule sensor frees the worker while Snowflake processes.
5. Idempotent MERGE — safe to replay any batch.
6. No pandas. No DataFrames. No transforms in Airflow.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import snowflake.connector
from cryptography.hazmat.primitives import serialization

from airflow import DAG
from airflow.exceptions import AirflowFailException, AirflowSkipException
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor

log = logging.getLogger(__name__)

CONFIG = {
    "api_base_url": os.getenv("TICKETING_API_BASE_URL", "http://mock-api:8099"),
    "api_token": os.getenv("TICKETING_API_TOKEN", "dev-token-events-2026"),
    "api_page_size": int(os.getenv("TICKETING_API_PAGE_SIZE", "100")),
    "api_max_retries": int(os.getenv("TICKETING_API_MAX_RETRIES", "3")),
    "api_backoff_base": float(os.getenv("TICKETING_API_BACKOFF_BASE", "2.0")),
    "api_timeout": int(os.getenv("TICKETING_API_TIMEOUT_SEC", "60")),

    "snowflake_user": os.getenv("SNOWFLAKE_USER"),
    "snowflake_account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "snowflake_private_key_path": os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "/opt/airflow/secrets/rsa_key.p8"),
    "snowflake_warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    "snowflake_database": os.getenv("SNOWFLAKE_DATABASE", "EVENTS_DEV"),
    "snowflake_role": os.getenv("SNOWFLAKE_ROLE", "EVENTS_DEV_ROLE"),

    "named_stage": os.getenv("SNOWFLAKE_NAMED_STAGE", "EVENTS_DEV.RAW.TICKETING_STAGE"),
    "batch_audit_table": os.getenv("BATCH_AUDIT_TABLE", "EVENTS_DEV.ORCH.BATCH_AUDIT"),
    "register_proc": os.getenv("REGISTER_BATCH_PROC", "EVENTS_DEV.ORCH.REGISTER_BATCH"),
    "watermark_table": os.getenv("WATERMARK_TABLE", "EVENTS_DEV.ORCH.WATERMARKS"),

    "local_stage_dir": os.getenv("LOCAL_STAGE_DIR", "/opt/airflow/tmp/api_extracts"),
    "entity_name": os.getenv("ENTITY_NAME", "tickets"),
    "source_name": os.getenv("SOURCE_NAME", "eventhub_api"),

    "bronze_poll_interval": int(os.getenv("BRONZE_POLL_INTERVAL_SEC", "15")),
    "bronze_timeout": int(os.getenv("BRONZE_TIMEOUT_SEC", "600")),
}


def _load_private_key():
    key_path = CONFIG["snowflake_private_key_path"]
    if not key_path or not Path(key_path).exists():
        raise RuntimeError(f"Private key not found: {key_path}")
    with open(key_path, "rb") as f:
        p_key = serialization.load_pem_private_key(f.read(), password=None)
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _sf_conn():
    return snowflake.connector.connect(
        user=CONFIG["snowflake_user"],
        account=CONFIG["snowflake_account"],
        private_key=_load_private_key(),
        warehouse=CONFIG["snowflake_warehouse"],
        database=CONFIG["snowflake_database"],
        role=CONFIG["snowflake_role"],
    )


def _api_get(url: str, params: dict) -> dict:
    headers = {"Authorization": f"Bearer {CONFIG['api_token']}"}
    max_retries = CONFIG["api_max_retries"]
    backoff = CONFIG["api_backoff_base"]

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=CONFIG["api_timeout"])
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", backoff ** attempt))
                log.warning("RATE LIMITED | retry in %ds", wait)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            if attempt == max_retries:
                raise RuntimeError(f"API timeout after {max_retries} attempts")
            time.sleep(backoff ** attempt)
        except requests.exceptions.ConnectionError as e:
            if attempt == max_retries:
                raise RuntimeError(f"API connection error: {e}")
            time.sleep(backoff ** attempt)
        except requests.exceptions.HTTPError as e:
            if r.status_code >= 500:
                if attempt == max_retries:
                    raise RuntimeError(f"API server error {r.status_code}")
                time.sleep(backoff ** attempt)
            else:
                raise RuntimeError(f"API client error {r.status_code}: {r.text}")

    raise RuntimeError("API max retries exhausted")


def get_watermark(**context):
    with _sf_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT LAST_WATERMARK FROM {CONFIG['watermark_table']} WHERE ENTITY_NAME = %s",
                (CONFIG["entity_name"],),
            )
            row = cur.fetchone()

    watermark = row[0] if row and row[0] else None
    is_backfill = watermark is None
    log.info("WATERMARK | value=%s | is_backfill=%s", watermark, is_backfill)
    context["ti"].xcom_push(key="watermark", value=watermark)
    context["ti"].xcom_push(key="is_backfill", value=is_backfill)


def extract_tickets(**context):
    watermark = context["ti"].xcom_pull(task_ids="get_watermark", key="watermark")
    is_backfill = context["ti"].xcom_pull(task_ids="get_watermark", key="is_backfill")

    page_size = 500 if is_backfill else CONFIG["api_page_size"]
    params = {"page": 1, "per_page": page_size}
    if watermark:
        params["since"] = watermark

    log.info("EXTRACT START | watermark=%s | backfill=%s", watermark, is_backfill)

    all_tickets = []
    page = 1
    server_time = None

    while True:
        params["page"] = page
        body = _api_get(f"{CONFIG['api_base_url']}/api/v1/tickets", params)
        all_tickets.extend(body["data"])
        server_time = body["meta"].get("current_server_time")

        log.info("EXTRACT PAGE | page=%d/%d | records=%d",
                 page, body["meta"]["total_pages"], len(all_tickets))

        if not body["meta"].get("has_more", False) or page >= body["meta"]["total_pages"]:
            break
        page += 1

    if not all_tickets:
        log.info("EXTRACT EMPTY | No new tickets since %s", watermark)
        raise AirflowSkipException("No new tickets — skipping downstream")

    batch_id = str(uuid.uuid4())
    local_dir = Path(CONFIG["local_stage_dir"]) / f"batch_id={batch_id}"
    local_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_dir / "tickets.json"
    local_file.write_text(json.dumps({"data": all_tickets}), encoding="utf-8")

    log.info("EXTRACT DONE | batch=%s | records=%d", batch_id, len(all_tickets))

    context["ti"].xcom_push(key="batch_id", value=batch_id)
    context["ti"].xcom_push(key="local_file", value=str(local_file))
    context["ti"].xcom_push(key="record_count", value=len(all_tickets))
    context["ti"].xcom_push(key="new_watermark", value=server_time)


def upload_to_stage(**context):
    batch_id = context["ti"].xcom_pull(task_ids="extract_tickets", key="batch_id")
    local_file = context["ti"].xcom_pull(task_ids="extract_tickets", key="local_file")

    stage_path = f"{CONFIG['named_stage']}/batch_id={batch_id}"

    with _sf_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"PUT file://{local_file} @{stage_path} AUTO_COMPRESS=FALSE OVERWRITE=TRUE")
            cur.execute(f"ALTER STAGE {CONFIG['named_stage']} REFRESH")

    log.info("UPLOAD DONE | batch=%s | stage=@%s", batch_id, stage_path)
    context["ti"].xcom_push(key="stage_path", value=f"@{stage_path}/tickets.json")


def register_batch(**context):
    batch_id = context["ti"].xcom_pull(task_ids="extract_tickets", key="batch_id")
    stage_path = context["ti"].xcom_pull(task_ids="upload_to_stage", key="stage_path")
    record_count = context["ti"].xcom_pull(task_ids="extract_tickets", key="record_count")

    with _sf_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"CALL {CONFIG['register_proc']}(%s, %s, %s, %s, %s, %s)",
                (batch_id, CONFIG["source_name"], CONFIG["entity_name"],
                 stage_path, context["run_id"], record_count),
            )

    log.info("BATCH REGISTERED | batch=%s | expected=%d", batch_id, record_count)


def check_bronze_ready(**context):
    batch_id = context["ti"].xcom_pull(task_ids="extract_tickets", key="batch_id")
    try:
        with _sf_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT STATUS, ERROR_MESSAGE FROM {CONFIG['batch_audit_table']} WHERE BATCH_ID = %s",
                    (batch_id,),
                )
                row = cur.fetchone()
    except Exception as e:
        log.warning("BRONZE CHECK ERROR | %s (will retry)", e)
        return False

    if not row:
        return False

    status, error = row[0], row[1]
    if status == "FAILED":
        raise AirflowFailException(f"Bronze load FAILED: {error}")
    return status == "BRONZE_COMPLETE"


def advance_watermark(**context):
    batch_id = context["ti"].xcom_pull(task_ids="extract_tickets", key="batch_id")
    new_watermark = context["ti"].xcom_pull(task_ids="extract_tickets", key="new_watermark")

    with _sf_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                MERGE INTO {CONFIG['watermark_table']} t
                USING (SELECT %s AS entity, %s AS wm, %s AS bid) s
                ON t.ENTITY_NAME = s.entity
                WHEN MATCHED THEN UPDATE SET
                    LAST_WATERMARK = s.wm,
                    LAST_BATCH_ID = s.bid,
                    UPDATED_AT = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN INSERT (ENTITY_NAME, LAST_WATERMARK, LAST_BATCH_ID, UPDATED_AT)
                    VALUES (s.entity, s.wm, s.bid, CURRENT_TIMESTAMP())
            """, (CONFIG["entity_name"], new_watermark, batch_id))

    log.info("WATERMARK ADVANCED | entity=%s | new=%s", CONFIG["entity_name"], new_watermark)


def cleanup_local(**context):
    batch_id = context["ti"].xcom_pull(task_ids="extract_tickets", key="batch_id")
    if not batch_id:
        return
    local_dir = Path(CONFIG["local_stage_dir"]) / f"batch_id={batch_id}"
    if local_dir.exists():
        import shutil
        shutil.rmtree(local_dir)
        log.info("CLEANUP | removed %s", local_dir)


DEFAULT_ARGS = {
    "owner": "events-data-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=15),
}

with DAG(
    dag_id="eventhub_single_source_pipeline",
    default_args=DEFAULT_ARGS,
    description="EventHub CDC: API → Stage → Stream → Triggered Task → Bronze",
    start_date=datetime(2026, 6, 28),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["eventhub", "cdc", "incremental", "snowflake"],
    doc_md=__doc__,
) as dag:

    t_watermark = PythonOperator(task_id="get_watermark", python_callable=get_watermark)
    t_extract = PythonOperator(task_id="extract_tickets", python_callable=extract_tickets)
    t_upload = PythonOperator(task_id="upload_to_stage", python_callable=upload_to_stage)
    t_register = PythonOperator(task_id="register_batch", python_callable=register_batch)

    t_wait_bronze = PythonSensor(
        task_id="wait_for_bronze",
        python_callable=check_bronze_ready,
        poke_interval=CONFIG["bronze_poll_interval"],
        timeout=CONFIG["bronze_timeout"],
        mode="reschedule",
    )

    t_advance = PythonOperator(task_id="advance_watermark", python_callable=advance_watermark)
    t_cleanup = PythonOperator(task_id="cleanup_local", python_callable=cleanup_local, trigger_rule="all_done")

    t_watermark >> t_extract >> t_upload >> t_register >> t_wait_bronze >> t_advance >> t_cleanup
