# CRIP — Cyber Risk Intelligence Platform

AI-powered SaaS platform that ingests asset and vulnerability data, builds a knowledge graph, and uses LLM-driven reasoning to surface attack paths, coverage gaps, and remediation priorities.

## Architecture

| Service | Port | Purpose |
|---------|------|---------|
| **Ingestion** | 8000 | Connector framework, asset/vuln ingestion into Neo4j |
| **Reasoning** | 8001 | RAG pipeline: intent classification, graph traversal, LLM generation |
| **Persona** | 8002 | APT persona management and kill-chain simulation |
| **Dashboard** | 8003 | Risk scoring, heatmaps, findings, report generation |
| **Frontend** | 5173 | React SPA |

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- An Anthropic API key (for the reasoning service)

## Quick Start

```bash
# 1. Copy environment config
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# 2. Start infrastructure (Neo4j, DynamoDB Local, LocalStack)
make up

# 3. Install all dependencies
make install

# 4. Run services (each in its own terminal)
make dev-ingestion
make dev-reasoning
make dev-persona
make dev-dashboard

# 5. Start frontend
cd frontend && npm run dev
```

## Local Infrastructure

| Container | Ports | Notes |
|-----------|-------|-------|
| Neo4j | 7474 (browser), 7687 (bolt) | Auth: neo4j / crip-local, APOC enabled |
| DynamoDB Local | 8000 | No auth required |
| LocalStack | 4566 | S3, SQS, EventBridge |

## Testing

```bash
make test    # Run all tests
make lint    # Ruff + ESLint
make typecheck  # mypy + tsc
```

## Project Layout

```
shared/          Pydantic schemas and shared utilities (installed as crip-shared)
services/
  ingestion/     Connector framework and graph ingestion
  reasoning/     RAG pipeline with Claude
  persona/       APT persona CRUD and kill-chain simulation
  dashboard/     Metrics, findings, reports
frontend/        React 18 + Vite + TailwindCSS
infra/           AWS CDK v2 stacks
```
