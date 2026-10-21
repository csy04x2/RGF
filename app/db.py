
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """RGF MySQL 데이터베이스에 연결합니다."""

    password = os.getenv("MYSQL_PASSWORD")

    if not password:
        raise ValueError(
            "MYSQL_PASSWORD가 설정되지 않았습니다. .env 파일을 확인하세요."
        )

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=password,
        database=os.getenv("MYSQL_DATABASE", "rgf"),
    )
