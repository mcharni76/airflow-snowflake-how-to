# Airflow + Snowflake: The Right Way — Decisions Log

### 2026-06-28 — Separation of Concerns: Airflow as Control Plane Only
| Aspect | Details |
|--------|---------|
| **Decision** | Airflow never transforms data. It only: calls APIs, uploads files, and observes completion. |
| **Rationale** | Keeps Airflow lightweight, stateless, and replaceable. Snowflake handles compute. |
| **Alternatives** | (a) Airflow PythonOperator with pandas transforms, (b) Airflow + Spark |
| **Impact** | DAG code is simple (no business logic). All logic lives in Snowflake SQL/dbt. |
| **Status** | Active |

### 2026-06-28 — Internal Stage for Local Development
| Aspect | Details |
|--------|---------|
| **Decision** | Use Snowflake internal named stage (not S3/GCS) for the hands-on lab |
| **Rationale** | Zero cloud bucket setup. Works with any Snowflake trial account. |
| **Alternatives** | (a) S3 + external stage, (b) Local Minio pretending to be S3 |
| **Impact** | PUT command from Airflow. Swappable to external stage for production (Bonus 2). |
| **Status** | Active |

### 2026-06-28 — Triggered Task (not Scheduled Task)
| Aspect | Details |
|--------|---------|
| **Decision** | Bronze loading uses a stream-triggered task, not a cron-scheduled task |
| **Rationale** | Event-driven: runs immediately when files land. No wasted compute polling empty stages. |
| **Alternatives** | (a) Scheduled task every 1 min, (b) Snowpipe (serverless), (c) Airflow sensor + COPY INTO |
| **Impact** | Requires directory stream + WHEN clause. Task can suspend on errors (gotcha). |
| **Status** | Active |

### 2026-06-28 — Watermark in Snowflake Table (not Airflow XCom)
| Aspect | Details |
|--------|---------|
| **Decision** | Store extraction watermark in a dedicated Snowflake table (ORCH.WATERMARKS) |
| **Rationale** | Survives DAG redeployment, Airflow metadata DB reset. Single source of truth. |
| **Alternatives** | (a) Airflow XCom, (b) Airflow Variables, (c) S3 marker file |
| **Impact** | Airflow queries Snowflake at DAG start for last watermark. Adds one SQL call. |
| **Status** | Active |

### 2026-06-28 — Generic Domain (not Saudi-specific)
| Aspect | Details |
|--------|---------|
| **Decision** | Use generic event ticketing (EventHub, TicketFlow, LivePass) not KSA platforms |
| **Rationale** | Wider audience. No trademark issues. Publishable on personal GitHub. |
| **Alternatives** | (a) Keep KSA branding (Webook, Tazkarti), (b) E-commerce domain, (c) IoT domain |
| **Impact** | All platform names, events, currencies are fictional. USD not SAR. |
| **Status** | Active |

### 2026-06-28 — SPCS as Primary Enterprise Deployment (Bonus 1)
| Aspect | Details |
|--------|---------|
| **Decision** | Position SPCS as the "keep everything in Snowflake" deployment option |
| **Rationale** | Unique differentiator. Zero-egress, single RBAC, one bill. No extra cloud vendor. |
| **Alternatives** | (a) Skip SPCS, only cover MWAA, (b) K8s Helm chart, (c) Astronomer |
| **Impact** | Requires multi-container service spec, compute pool, network rules, secrets. |
| **Status** | Active |
