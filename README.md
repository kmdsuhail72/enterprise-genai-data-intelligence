# Enterprise GenAI Data Intelligence Platform

A production-grade, modular Enterprise Generative AI platform designed for automated ingestion, OCR, extraction, transformation, hybrid retrieval-augmented generation (RAG), and multi-provider LLM orchestration with verifiable source citations.

---

## 🏗️ Architecture Overview

The platform is designed in two primary deployment stages:
- **Stage A (Local Development)**: Docker Compose hosting PostgreSQL 16 + `pgvector`, local Ollama LLM/Embeddings, FastAPI backend, and Streamlit frontend.
- **Stage B (AWS Production)**: AWS S3, EventBridge, Step Functions, Lambda, Glue, Amazon Bedrock, ECS Fargate, RDS PostgreSQL (`pgvector`), Secrets Manager, CloudWatch, and Terraform IaC.

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit / Web UI                       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST
┌──────────────────────────────▼──────────────────────────────┐
│                       FastAPI Backend                       │
│  ┌───────────────────────┐        ┌───────────────────────┐ │
│  │ Document Ingestion &  │        │   Hybrid Retriever    │ │
│  │ Validation Pipeline   │        │ (pgvector + FTS RRF)  │ │
│  └───────────┬───────────┘        └───────────▲───────────┘ │
│              │                                │             │
│  ┌───────────▼───────────┐        ┌───────────┴───────────┐ │
│  │   Extraction & OCR    │        │  Multi-Provider LLM   │ │
│  │ (PyMuPDF, PaddleOCR)  │        │ (Bedrock/OpenAI/Oll)  │ │
│  └───────────┬───────────┘        └───────────┬───────────┘ │
│              │                                │             │
│  ┌───────────▼───────────┐        ┌───────────▼───────────┐ │
│  │   ETL & Chunking      │───────▶│   Citation Manager    │ │
│  │  (Recursive + Table)  │        │ & Evidence Linker     │ │
│  └───────────────────────┘        └───────────────────────┘ │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                 PostgreSQL 16 + pgvector                    │
│   • documents       • document_pages   • chunks (Vector)    │
│   • users           • queries          • document_access    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

The current implementation and its file-by-file dependency map are documented in
[docs/architecture/repository-structure.md](docs/architecture/repository-structure.md).
The tree below is a quick orientation; planned components are not represented as implemented.

```
Enterprise_GenAI_Data_Intelligence_Platform/
├── docs/architecture/          # Accepted architecture decision records and structure map
├── docker/                     # Local PostgreSQL/pgvector services and DB initialization
├── migrations/                 # Alembic environment and schema revisions
├── scripts/                    # Local database initialization utilities
├── src/enterprise_ai/          # FastAPI application and domain modules
└── tests/                      # Unit, API, and integration tests
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Python**: 3.11+
- **Docker**: Docker Desktop / Docker Engine with Compose
- **macOS (Apple Silicon) / Linux / Windows** supported

### 2. Environment Setup

#### On macOS / Linux:
```bash
# Clone the repository and navigate into it
cd Enterprise_GenAI_Data_Intelligence_Platform

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Create the local environment file only if it does not already exist
if [ ! -f .env ]; then cp .env.example .env; fi

# Install base and development dependencies
pip install -e ".[dev]"
```

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
pip install -e ".[dev]"
```

### 3. Start Database & Ollama Services

Set a local-only `DB_PASSWORD` in `.env` before starting PostgreSQL. The optional
pgAdmin service has no default credentials; set `PGADMIN_DEFAULT_EMAIL` and
`PGADMIN_DEFAULT_PASSWORD` in `.env` before enabling its `admin` profile.

```bash
# Launch PostgreSQL 16 (with pgvector) and Ollama
docker compose -f docker/docker-compose.yml up -d
```

To include pgAdmin after setting its local credentials:

```bash
docker compose -f docker/docker-compose.yml --profile admin up -d
```

Verify that services are running:
```bash
docker ps
```

### 4. Run Database Migrations

```bash
# Generate the initial schema migration (if not already generated)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 5. Run Unit Tests

```bash
pytest tests/unit tests/api -v
```

### 6. Run the FastAPI Application

```bash
# Start the API server with live reloading
uvicorn enterprise_ai.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- Liveness check (does not require PostgreSQL): `http://localhost:8000/health`
- Readiness check (returns HTTP 503 if PostgreSQL is unavailable): `http://localhost:8000/ready`

Verify the probes from a terminal:

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ready
```

The API reads database settings from `DATABASE_URL` or the `DB_*` values in `.env`.
Use a local-only password in `.env`; `.env.example` intentionally contains no credentials.

---

## 🔒 Security & Enterprise Best Practices
- **Strict Role-Based Access Control (RBAC)**: Enforced via `UserRole` and document-level permissions (`document_access`).
- **PII Governance**: Pre-storage and pre-LLM redaction gates.
- **Provider Agnostic**: Unified interfaces for local Ollama, Amazon Bedrock, OpenAI, and Google Gemini.
- **Auditing & Cost Tracking**: Every query logs token usage, latency, provider/model, and calculated dollar cost.
