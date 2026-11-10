# ADR-001: Asynchronous FastAPI Backend Framework

## Status
Accepted

## Context
The platform requires high-throughput handling of concurrent document uploads, real-time RAG query streaming, authentication, and background worker coordination.

## Decision
Use **FastAPI** on Python 3.11+ with `uvicorn` and `asyncpg`.

## Consequences
- **Positive**: Native asynchronous I/O (`async/await`) prevents blocking during network calls to LLMs and database queries. Pydantic v2 ensures strict request/response data contracts and automated OpenAPI/Swagger generation.
- **Negative**: Requires careful handling of CPU-bound tasks (OCR, large PDF extraction) to avoid blocking the event loop; these must run in background threads, process pools, or worker containers.

