"""
Database Session
----------------

Database connections for AgentOS (PostgreSQL and SQLite).
"""

from functools import cache
from pathlib import Path

from agno.db.postgres import PostgresDb
from agno.db.sqlite import SqliteDb
from agno.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

from db.url import db_url, has_database_url

DB_ID = "agentos-db"
SQLITE_DB_ID = "agentos-sqlite-db"
SQLITE_DB_FILE = Path(__file__).parent / "sessions.db"


@cache
def get_sqlite_db() -> SqliteDb:
    """Return the shared SqliteDb instance backed by db/sessions.db (created on first use).

    Cached so every caller gets the same object — two instances with the same id make the
    AgentOS registry warn and keep only one.

    Returns:
        Configured SqliteDb instance.
    """
    return SqliteDb(id=SQLITE_DB_ID, db_file=str(SQLITE_DB_FILE))


@cache
def get_db() -> PostgresDb | SqliteDb:
    """Return the main AgentOS database: Postgres (e.g. Neon) when DATABASE_URL is set, else local SQLite."""
    if has_database_url():
        return PostgresDb(id="agentos-main-db", db_url=db_url)
    return get_sqlite_db()


def get_postgres_db(contents_table: str | None = None) -> PostgresDb:
    """Create a PostgresDb instance.

    Args:
        contents_table: Optional table name for storing knowledge contents.

    Returns:
        Configured PostgresDb instance.
    """
    if contents_table is not None:
        return PostgresDb(id=DB_ID, db_url=db_url, knowledge_table=contents_table)
    return PostgresDb(id=DB_ID, db_url=db_url)


def create_knowledge(name: str, table_name: str) -> Knowledge:
    """Create a Knowledge instance with PgVector hybrid search.

    Args:
        name: Display name for the knowledge base.
        table_name: PostgreSQL table name for vector storage.

    Returns:
        Configured Knowledge instance.
    """
    return Knowledge(
        name=name,
        vector_db=PgVector(
            db_url=db_url,
            table_name=table_name,
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        ),
        contents_db=get_postgres_db(contents_table=f"{table_name}_contents"),
    )
