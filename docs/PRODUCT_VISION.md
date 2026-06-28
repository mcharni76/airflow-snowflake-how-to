# Airflow + Snowflake: The Right Way — Product Vision

| Field | Value |
|-------|-------|
| Product | airflow-snowflake-how-to |
| Version | 0.1.0 |
| Last Updated | 2026-06-28 |
| Status | Development |

## Vision Statement
> "The definitive open-source reference for combining Airflow with Snowflake correctly — Airflow orchestrates, Snowflake executes."

## Target Users
| Persona | Description | Primary Needs |
|---------|-------------|---------------|
| Data Engineer | Building pipelines with Airflow + Snowflake | Production-grade patterns, not toy examples |
| Platform Engineer | Evaluating Airflow deployment options | SPCS vs MWAA vs self-hosted comparison |
| Tech Lead | Making architecture decisions | Clear separation of concerns, gotchas awareness |
| Learner | Following Medium series | Step-by-step progression with working code |

## Value Proposition
| For Users Who... | This Repo... |
|------------------|--------------|
| Over-engineer Airflow as executor | Shows the control-plane-only pattern |
| Need incremental CDC patterns | Provides watermark + stream + triggered task |
| Want to avoid common gotchas | Documents 10 real debugging war stories |
| Need enterprise deployment | Covers SPCS (zero-egress) and MWAA (managed) |

## Product Principles
1. **Working code over documentation** — every article has runnable code
2. **Progressive complexity** — start simple, add layers
3. **Production patterns** — nothing here is "demo-only"
4. **Honest about trade-offs** — alternatives discussed, not hidden

## What This Product Is NOT
- NOT a Snowflake tutorial (assumes basic Snowflake knowledge)
- NOT an Airflow beginner guide (assumes DAG familiarity)
- NOT a dbt course (covers integration, not dbt fundamentals)
- NOT vendor-specific (generic domain, works with any Snowflake account)
