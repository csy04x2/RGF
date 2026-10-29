
import os

import pytest
import pymysql

from app.database import get_connection


def test_database_connection():
    """Verify that RGF can connect to MySQL."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS db_name")
            result = cursor.fetchone()

        assert result["db_name"] == os.getenv("MYSQL_DATABASE")

    finally:
        connection.close()


def test_database_tables_exist():
    """Verify that all five RGF tables exist."""

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            rows = cursor.fetchall()

        tables = {
            next(iter(row.values()))
            for row in rows
        }

        expected = {
            "source_documents",
            "source_evidence",
            "analysis_runs",
            "article_ideas",
            "article_evidence",
        }

        assert expected.issubset(tables)

    finally:
        connection.close()
