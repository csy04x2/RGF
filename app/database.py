import os
from pathlib import Path

import pymysql
import psycopg
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from psycopg.rows import dict_row


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)




def is_postgres(connection):
    """Whether a connection is a real psycopg PostgreSQL connection."""
    return isinstance(connection, psycopg.Connection)


def get_connection():
    """Connect to PostgreSQL or the existing local MySQL."""

    database_url = os.getenv("DATABASE_URL")

    # Railway PostgreSQL
    if database_url:
        return psycopg.connect(
            database_url,
            row_factory=dict_row,
            connect_timeout=5,
        )

    # Existing local MySQL
    if os.getenv("DATABASE_URL"):
        return psycopg.connect(
            os.environ["DATABASE_URL"], row_factory=dict_row, connect_timeout=5
        )

    required = [
        "MYSQL_HOST",
        "MYSQL_DATABASE",
        "MYSQL_USER",
        "MYSQL_PASSWORD",
    ]

    missing = [
        key for key in required
        if os.getenv(key) is None
    ]

    if missing:
        raise RuntimeError(
            "DB 연결 환경변수가 없습니다: "
            + ", ".join(missing)
        )

    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
    )