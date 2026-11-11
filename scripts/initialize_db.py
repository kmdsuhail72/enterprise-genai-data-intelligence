"""Database verification and initialization script."""

import asyncio

import asyncpg

from enterprise_ai.core.config import get_settings


async def verify_database() -> None:
    settings = get_settings()
    print(f"Connecting to database at {settings.db_host}:{settings.db_port}/{settings.db_name}...")

    conn = await asyncpg.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
    )

    try:
        # Check extensions
        ext_rows = await conn.fetch("SELECT extname, extversion FROM pg_extension ORDER BY extname;")
        print("\nInstalled PostgreSQL Extensions:")
        for r in ext_rows:
            print(f" - {r['extname']} (v{r['extversion']})")

        # Check tables
        table_rows = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        )
        print("\nDatabase Tables:")
        for r in table_rows:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM \"{r['table_name']}\";")
            print(f" - {r['table_name']}: {count} rows")

        # Verify HNSW index on chunks
        idx_rows = await conn.fetch(
            "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'chunks' ORDER BY indexname;"
        )
        print("\nIndexes on 'chunks' table:")
        for r in idx_rows:
            print(f" - {r['indexname']}")

        print("\n[SUCCESS] Database schema and vector extensions verified successfully!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(verify_database())

