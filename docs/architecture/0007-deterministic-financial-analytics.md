# ADR-007: Deterministic Computation Engine for Numerical and Financial Queries

## Status
Accepted

## Context
LLMs are probabilistic token predictors and frequently hallucinate or err when performing complex arithmetic (e.g. percentage growth across periods, margin calculations, multi-row aggregations).

## Decision
Route numerical and comparison queries through a **Deterministic Execution Engine** (Python Pandas / SQL) rather than asking the LLM to compute math in its autoregressive prompt. The LLM is used to synthesize and explain findings, but the numbers originate from deterministic calculations.

## Consequences
- **Positive**: 100% mathematical accuracy on financial reports, audits, and compliance comparisons. Citations link directly to exact cell coordinates.
- **Negative**: Requires structured table extraction and query classification before generation.

