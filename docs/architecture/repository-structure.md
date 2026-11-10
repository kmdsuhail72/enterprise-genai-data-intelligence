# Repository Structure and Dependency Map

This document records the repository layout after approval of the local-first platform architecture. It distinguishes files present in the repository from capabilities planned for later phases. The tree and dependency map describe the current implementation; a named module is not considered implemented merely because it appears in the architecture.

## Repository map

```text
Enterprise_GenAI_Data_Intelligence_Platform/
├── .dockerignore                         # Files excluded from Docker build contexts
├── .env.example                          # Documented local configuration template
├── .gitignore                             # Generated, local, and secret-file exclusions
├── .pre-commit-config.yaml                # Pre-commit quality hooks
├── LICENSE                                # Repository license
├── Makefile                               # Common developer commands
├── README.md                              # Product overview and local quickstart
├── alembic.ini                            # Alembic configuration
├── pyproject.toml                         # Package metadata, dependencies, and tool config
├── requirements.txt                       # Runtime dependency list
├── requirements-dev.txt                   # Development dependency list
├── data/
│   └── samples/sample_financial.csv       # Small sample for local analytics/testing
├── docker/
│   ├── docker-compose.yml                 # Local service definitions
│   └── init-db.sql                        # Database extensions/bootstrap SQL
├── docs/
│   └── architecture/
│       ├── README.md                      # ADR index
│       ├── 0001-fastapi-backend.md        # FastAPI decision
│       ├── 0002-postgresql-pgvector.md    # PostgreSQL/pgvector decision
│       ├── 0003-hybrid-retrieval-rrf.md   # Hybrid retrieval decision
│       ├── 0007-deterministic-financial-analytics.md # Deterministic analytics decision
│       └── repository-structure.md        # This structure and dependency map
├── migrations/
│   ├── env.py                             # Alembic database/migration integration
│   ├── script.py.mako                     # Migration file template
│   └── versions/
│       └── 323dddc277a4_initial_enterprise_schema.py # Initial schema revision
├── scripts/
│   └── initialize_db.py                   # Local database initialization entry point
├── src/
│   ├── __init__.py                        # Source package marker
│   └── enterprise_ai/
│       ├── main.py                        # FastAPI app factory and lifecycle
│       ├── api/
│       │   ├── dependencies.py            # API-layer dependency providers
│       │   ├── middleware/
│       │   │   ├── __init__.py            # Middleware exports
│       │   │   ├── authentication.py       # Authentication middleware
│       │   │   ├── error_handler.py        # HTTP exception/error translation
│       │   │   └── request_logging.py      # Request-scoped logging
│       │   └── routes/
│       │       ├── __init__.py             # API router composition
│       │       ├── admin.py                # Administrative endpoints
│       │       ├── analytics.py            # Analytics endpoints
│       │       ├── chat.py                 # Question/answer endpoints
│       │       ├── documents.py            # Document upload and status endpoints
│       │       └── health.py               # Health endpoints
│       ├── core/
│       │   ├── __init__.py                 # Core package marker
│       │   ├── config.py                   # Typed application settings
│       │   ├── constants.py                # Shared constants and enums
│       │   ├── dependencies.py              # Shared dependency helpers
│       │   ├── exceptions.py                # Domain/application exception types
│       │   ├── logging.py                   # Logging setup and logger factory
│       │   └── security.py                  # Shared security helpers
│       ├── database/
│       │   ├── base.py                      # ORM base and database models
│       │   ├── connection.py                # Async engine/session lifecycle
│       │   └── repositories/
│       │       ├── base.py                  # Shared repository operations
│       │       ├── chunk_repository.py      # Chunk persistence and retrieval queries
│       │       ├── document_repository.py   # Document persistence and lookups
│       │       └── user_repository.py       # User persistence and lookups
│       ├── extraction/
│       │   ├── __init__.py                  # Extraction package exports
│       │   ├── base_extractor.py            # Extractor contract/shared behavior
│       │   ├── csv_extractor.py             # CSV parsing
│       │   ├── docx_extractor.py            # Word document parsing
│       │   ├── excel_extractor.py           # Excel workbook parsing
│       │   ├── image_extractor.py           # Image input extraction/OCR coordination
│       │   ├── layout_analyzer.py           # Page/layout analysis
│       │   ├── models.py                    # Extraction-domain models
│       │   ├── ocr_engine.py                # OCR engine adapter
│       │   ├── pdf_extractor.py             # PDF page/text extraction
│       │   ├── router.py                    # File-type extractor selection
│       │   ├── schemas.py                   # Extraction result schemas
│       │   └── table_extractor.py            # Table detection and normalization
│       ├── ingestion/
│       │   ├── checksum.py                  # Content checksum calculation
│       │   ├── file_validator.py             # Upload type/size/content validation
│       │   ├── ingestion_service.py          # Upload orchestration and document record creation
│       │   ├── local_storage.py              # Local filesystem storage adapter
│       │   ├── s3_storage.py                 # S3 storage adapter
│       │   ├── service.py                    # Legacy/overlapping ingestion implementation
│       │   ├── status_manager.py             # Processing status transitions
│       │   ├── storage.py                    # Legacy/overlapping storage implementation
│       │   ├── storage_interface.py          # Storage adapter contract
│       │   └── upload_service.py              # Validation, checksum, and storage coordination
│       ├── schemas/
│       │   ├── __init__.py                   # Schema package exports
│       │   ├── analytics.py                  # Analytics request/response models
│       │   ├── chat.py                       # Chat request/response models
│       │   ├── common.py                     # Shared API schema types
│       │   ├── document.py                   # Document request/response models
│       │   ├── evaluation.py                 # Evaluation data models
│       │   └── user.py                       # User request/response models
│       └── services/
│           ├── __init__.py                   # Service package exports
│           ├── analytics_service.py          # Analytics use-case orchestration
│           ├── chat_service.py               # Chat use-case orchestration
│           ├── document_service.py           # Document use-case orchestration
│           ├── processing_service.py         # Extraction and persistence workflow
│           └── user_service.py                # User use-case orchestration
└── tests/
    ├── __init__.py                           # Test package marker
    ├── conftest.py                           # Shared pytest fixtures
    ├── fixtures/.gitkeep                    # Placeholder for test-only fixtures
    ├── api/
    │   ├── test_chat_api.py                  # Chat endpoint behavior
    │   └── test_documents_api.py             # Document endpoint behavior
    ├── integration/
    │   ├── __init__.py                       # Integration-test package marker
    │   └── test_ingestion.py                 # Ingestion workflow integration tests
    └── unit/
        ├── __init__.py                       # Unit-test package marker
        ├── test_config.py                    # Configuration validation
        ├── test_exceptions.py                # Exception behavior
        ├── test_extraction.py                # Extractor behavior
        └── test_models.py                    # ORM model behavior
```

Local-only `.env` files, uploaded documents, Python bytecode, test caches, and Git internals are intentionally excluded from this map. They are runtime or generated state, not application source.

## Dependency boundaries

The dependency direction is inward: HTTP adapters call application services; services coordinate domain work and persistence; repositories own database access; provider and storage implementations sit behind narrow interfaces. Core configuration, logging, errors, and shared types may be used by outer layers, but should not depend on route handlers.

```text
HTTP client
    │
    ▼
api/routes + api/middleware
    │ request/response schemas, injected session/settings
    ▼
services
    ├── ingestion ──► file_validator / checksum / storage interface
    │                    ├── local_storage
    │                    └── s3_storage
    ├── processing ─► extraction/router ─► format-specific extractors
    │                                      ├── OCR/layout/table helpers
    │                                      └── extraction schemas/models
    ├── chat / analytics / document / user use cases
    ▼
database/repositories
    ▼
database models + async connection
    ▼
PostgreSQL / pgvector

core config, logging, exceptions, constants, and security helpers
    └── shared by the application layers; must not import API routes
```

### Package-level contract

| Area | Owns | May depend on | Must not own |
|---|---|---|---|
| `api/` | HTTP routing, middleware, request/response adaptation | `services/`, `schemas/`, `core/` | SQL query construction or document parsing |
| `services/` | Application use cases and transaction/workflow coordination | `database/repositories/`, `ingestion/`, `extraction/`, `schemas/`, `core/` | HTTP response objects or provider SDK details |
| `ingestion/` | Upload validation, checksum, file storage, status coordination | `core/`, configured storage adapter, document repository | HTTP routing or extraction format internals |
| `extraction/` | Format-specific parsing and normalized extraction results | Extraction libraries, `core/`, extraction schemas/models | Database commits or API response formatting |
| `database/` | ORM schema, engine/session, persistence queries | SQLAlchemy, pgvector, `core/` configuration | LLM prompting or file parsing |
| `schemas/` | Typed request/response and domain data contracts | Pydantic and standard types | I/O, persistence, or provider calls |
| `core/` | Cross-cutting settings, logging, errors, shared security primitives | Standard library and foundational dependencies | Imports from feature packages |
| `tests/` | Verification of public behavior and module contracts | Application modules and pytest fixtures | Production behavior or test-only imports in application code |

### Existing overlap to resolve deliberately

`ingestion/service.py` and `ingestion/storage.py` overlap with the canonical `ingestion_service.py`, `upload_service.py`, `storage_interface.py`, `local_storage.py`, and `s3_storage.py`. The former files import the older `app.*` package path, while the active application package is `enterprise_ai`. Treat the `enterprise_ai` package as canonical; do not add new code against the old imports. Consolidate or remove the overlapping files in a separately tested cleanup rather than mixing that change into the repository-map update.

## Planned modules, not yet present

The approved architecture calls for capabilities that are not represented by the current files. Add them incrementally under `src/enterprise_ai/` when implementing those features:

| Planned area | Responsibility | Depends on |
|---|---|---|
| `chunking/` | Split extracted text/tables while retaining page and source metadata | `extraction/`, shared chunk contracts |
| `embeddings/` | Embedding interface and selected local/cloud adapters | Provider configuration and chunk contracts |
| `retrieval/` | Permission-filtered vector + keyword search, fusion, reranking, context assembly | `database/repositories/`, `embeddings/`, access-control policy |
| `providers/` | Common generation interface and Ollama, Bedrock, OpenAI, Gemini adapters | Provider SDKs, `core/config.py` |
| `citations/` | Validate evidence references and map claims to source metadata | Retrieval results, persisted documents/pages |
| `analytics/` | Deterministic financial query planning and calculations | Structured extracted data, repositories |
| `evaluation/` | Retrieval/answer datasets, metrics, and run records | Retrieval, citations, provider abstractions |
| `frontend/` | Initial Streamlit user interface | Public API contracts only |
| `infrastructure/` | Terraform modules/environments and deployment assets | AWS architecture and environment configuration |

The planned feature modules must remain separately testable and should not be added as empty placeholders. In particular, authorization filtering belongs before retrieval context is constructed, and financial calculations must remain deterministic rather than delegated to an LLM.

## Change conventions

1. Keep the import package rooted at `enterprise_ai`; do not recreate the stale `src/app/` tree.
2. Keep route handlers thin and put business orchestration in `services/`.
3. Keep provider and storage SDK code behind interfaces/adapters.
4. Preserve document, page, table, and extraction metadata through every transformation.
5. Add a focused unit or integration test beside the behavior being introduced.
6. Update this document when adding a top-level package or changing a dependency boundary.
