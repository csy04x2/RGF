
import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def get_connection():
    """Create a connection to the RGF MySQL database."""

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
            "MySQL 환경변수가 없습니다: "
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
