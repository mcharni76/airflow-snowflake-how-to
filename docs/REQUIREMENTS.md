# Airflow + Snowflake: The Right Way — Requirements

## Functional Requirements
| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR001 | Single-source incremental CDC pipeline (watermark-based) | Must | Planned |
| FR002 | Multi-source parallel ingestion (3 APIs, TaskGroups) | Must | Planned |
| FR003 | dbt transformation layer (Bronze → Silver → Gold) | Must | Planned |
| FR004 | Mock APIs that simulate real vendor behavior | Must | Planned |
| FR005 | Snowflake triggered task for event-driven Bronze loading | Must | Planned |
| FR006 | SPCS deployment spec for enterprise Airflow | Must | Planned |
| FR007 | MWAA migration guide with S3 + Snowpipe | Must | Planned |
| FR008 | Gotchas documentation with before/after fixes | Must | Planned |
| FR009 | Streamlit monitoring dashboard | Should | Planned |
| FR010 | Automated test suite (unit + E2E) | Should | Planned |

## Non-Functional Requirements

### Security
| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-SEC-001 | No secrets in code or git history | .env + .gitignore + .env.example pattern |
| NFR-SEC-002 | Key-pair authentication (not password) | .p8 private key mounted read-only |
| NFR-SEC-003 | Dedicated role (not ACCOUNTADMIN) for runtime | EVENTS_DEV_ROLE with minimum grants |

### Portability
| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-PORT-001 | Works with any Snowflake account (trial included) | Internal stage, no S3 dependency |
| NFR-PORT-002 | No region/cloud-specific dependencies | Generic domain, no AWS/GCP services required |
| NFR-PORT-003 | Docker-only local prerequisites | docker-compose.yaml handles everything |

### Documentation
| ID | Requirement | Implementation |
|----|-------------|----------------|
| NFR-DOC-001 | Every article has corresponding runnable code | Git tags match article publications |
| NFR-DOC-002 | Architecture diagrams in Mermaid (reproducible) | docs/diagrams/ |
| NFR-DOC-003 | Gotchas documented with root cause + fix | GOTCHAS.md |

## Constraints
| Constraint | Description | Impact |
|------------|-------------|--------|
| No vendor branding | Cannot use real ticketing platform names/logos | Use fictional names (EventHub, TicketFlow, LivePass) |
| Personal GitHub | Published under personal account, not Snowflake org | MIT license, no Snowflake IP |
| Medium format | Articles must be 8-12 min read | Split content across 7 articles |
| Progressive disclosure | Repo grows with each article | Git tags required at each publish |
