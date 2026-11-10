# ADR-002: PostgreSQL 16 + pgvector for Unified Knowledge Store

## Status
Accepted

## Context
Enterprise document analytics requires transactional consistency for RBAC, tenancy, document status, and query audit trails, alongside high-dimensional vector similarity search and lexical text search.

## Decision
Use **PostgreSQL 16** with the **pgvector** and **pg_trgm** extensions as the primary datastore.

## Consequences
- **Positive**: Eliminates multi-database operational complexity and synchronization failures between a relational DB and a standalone vector DB (such as Pinecone or Milvus). ACID transactions guarantee document-level permissions before retrieval. Zero SaaS subscription cost.
- **Negative**: Scale limits for billions of vectors require database tuning or read-replicas; however, for hundreds of thousands of enterprise chunks, HNSW indexes in pgvector achieve single-digit millisecond latency.

