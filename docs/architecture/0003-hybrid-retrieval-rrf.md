# ADR-003: Hybrid Retrieval using Vector Search + Full-Text Search with RRF

## Status
Accepted

## Context
Pure vector (dense semantic) search struggles with exact keywords, part numbers, specific dates, and exact financial table metrics. Pure lexical (sparse BM25/FTS) search misses conceptual context and synonyms.

## Decision
Implement **Hybrid Retrieval** combining `pgvector` cosine similarity with PostgreSQL native `tsvector`/`tsquery` full-text search, fused using **Reciprocal Rank Fusion (RRF)**:
$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
where $k = 60$ and $r_m(d)$ is the rank of document $d$ under model $m$.

## Consequences
- **Positive**: Significantly higher recall on complex enterprise queries that mix exact financial identifiers (e.g. "FY2025 Segment A EBITDA") with semantic queries ("factors driving revenue expansion").
- **Negative**: Requires generating both dense embeddings and `tsvector` representations during ingestion.

