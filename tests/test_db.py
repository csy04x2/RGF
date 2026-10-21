
from unittest.mock import MagicMock, patch

import pytest

from app.db import get_connection


def test_db_connection_settings(monkeypatch):
    """DB 연결 함수가 환경변수를 올바르게 사용하는지 검사한다."""

    monkeypatch.setenv("MYSQL_HOST", "127.0.0.1")
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setenv("MYSQL_USER", "root")
    monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
    monkeypatch.setenv("MYSQL_DATABASE", "rgf")

    with patch("app.db.mysql.connector.connect") as mock_connect:
        mock_connect.return_value = MagicMock()

        get_connection()

        mock_connect.assert_called_once_with(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="test_password",
            database="rgf",
        )


def test_db_password_required(monkeypatch):
    """DB 비밀번호가 없으면 연결을 시도하지 않아야 한다."""

    monkeypatch.delenv("MYSQL_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="MYSQL_PASSWORD"):
        get_connection()
