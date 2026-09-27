"""
Database URL
------------

Build database connection URL from environment variables.
"""

import re
from os import getenv
from urllib.parse import quote


def build_db_url() -> str:
    """Build database URL from environment variables.

    DATABASE_URL (e.g. a Neon connection string) wins when set; otherwise DB_* variables are used.
    """
    url = getenv("DATABASE_URL")
    if url:
        # Tolerate copy/paste noise: quotes, spaces, newlines or a "psql '...'" prefix (Neon's Connect box)
        match = re.search(r"postgres(?:ql)?://[^\s'\"]+", url)
        if match:
            url = match.group(0)
            # Neon/Heroku style "postgres://" or "postgresql://" -> SQLAlchemy psycopg driver
            return "postgresql+psycopg://" + url.split("://", 1)[1]
        return url.strip()

    driver = getenv("DB_DRIVER", "postgresql+psycopg")
    user = getenv("DB_USER", "ai")
    password = quote(getenv("DB_PASS", "ai"), safe="")
    host = getenv("DB_HOST", "localhost")
    port = getenv("DB_PORT", "5432")
    database = getenv("DB_DATABASE", "ai")

    return f"{driver}://{user}:{password}@{host}:{port}/{database}"


db_url = build_db_url()
