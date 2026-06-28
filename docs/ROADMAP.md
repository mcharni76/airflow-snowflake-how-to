# Airflow + Snowflake: The Right Way — Roadmap

| Field | Value |
|-------|-------|
| Last Updated | 2026-06-28 |
| Current Phase | v0.1 (Core Series) |

## v0.1 — Core Series (5 Articles)

### Must Have
| ID | Feature | Status | Tag |
|----|---------|--------|-----|
| F001 | Article 1: Architecture philosophy + README | [ ] In Progress | repo-live |
| F002 | Article 2: Single-source DAG + mock API + Snowflake objects | [ ] Planned | v0.1 |
| F003 | Article 3: dbt Silver + Gold models | [ ] Planned | v0.2 |
| F004 | Article 4: Multi-source DAG + 3 mock APIs | [ ] Planned | v0.3 |
| F005 | Article 5: Gotchas + architecture alternatives | [ ] Planned | v0.4 |

### Should Have
| ID | Feature | Status | Notes |
|----|---------|--------|-------|
| F101 | Streamlit monitoring dashboard | [ ] Planned | Optional, included in repo |
| F102 | Unit + E2E test suite | [ ] Planned | Must pass before each tag |
| F103 | Mermaid architecture diagrams | [ ] Planned | For articles and docs/ |

## v1.0 — Bonus Articles (Enterprise Deployment)

### Must Have
| ID | Feature | Status | Tag |
|----|---------|--------|-----|
| F201 | Bonus 1: SPCS deployment (Dockerfile, spec, setup SQL) | [ ] Planned | v1.0-spcs |
| F202 | Bonus 2: MWAA migration (external stage, Snowpipe, DAG diff) | [ ] Planned | v1.0-mwaa |

### Should Have
| ID | Feature | Status | Notes |
|----|---------|--------|-------|
| F301 | SPCS compute pool auto-scaling demo | [ ] Planned | Enterprise feature highlight |
| F302 | Cost comparison calculator | [ ] Planned | SPCS vs MWAA vs self-hosted |

## Won't Have (This Version)
| ID | Feature | Reason |
|----|---------|--------|
| F901 | React dashboard | Out of scope for article series |
| F902 | Kafka/Snowpipe Streaming integration | Overkill for learning material |
| F903 | Multi-account deployment | Too advanced for series scope |
| F904 | CI/CD pipeline (GitHub Actions) | Distracts from core patterns |

## Backlog (Future Versions)
| ID | Feature | Target | Priority |
|----|---------|--------|----------|
| B001 | Video walkthrough per article | v2.0 | Medium |
| B002 | Terraform/Pulumi for Snowflake objects | v2.0 | Low |
| B003 | Observability (Prometheus + Grafana for Airflow) | v2.0 | Low |
