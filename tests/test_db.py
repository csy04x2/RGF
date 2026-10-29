
from unittest.mock import patch

import pytest

from app.database import get_connection


def test_db_connection_settings(monkeypatch):
    """DB 연결 시 환경변수가 올바르게 전달되는지 검사한다."""

    monkeypatch.setenv("MYSQL_HOST", "127.0.0.1")
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setenv("MYSQL_USER", "root")
    monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
    monkeypatch.setenv("MYSQL_DATABASE", "rgf")

    with patch("app.database.pymysql.connect") as mock_connect:
        get_connection()

    mock_connect.assert_called_once()

    kwargs = mock_connect.call_args.kwargs

    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 3306
    assert kwargs["user"] == "root"
    assert kwargs["password"] == "test_password"
    assert kwargs["database"] == "rgf"
    assert kwargs["charset"] == "utf8mb4"
    assert kwargs["autocommit"] is False


def test_db_password_required(monkeypatch):
    """DB 비밀번호가 없으면 연결을 시도하지 않아야 한다."""

    monkeypatch.delenv("MYSQL_PASSWORD", raising=False)

    with patch("app.database.pymysql.connect") as mock_connect:
        with pytest.raises(RuntimeError, match="MYSQL_PASSWORD"):
            get_connection()

    mock_connect.assert_not_called()
