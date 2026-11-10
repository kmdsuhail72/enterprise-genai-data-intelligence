-- =============================================================================
-- Enterprise GenAI Data Intelligence Platform — Database Initialization
-- =============================================================================
-- This script runs automatically when the PostgreSQL container is first created.
-- It enables required extensions for vector similarity search and trigram matching.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
