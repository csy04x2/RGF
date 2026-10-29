
from unittest.mock import MagicMock, patch

from app.source_repository import (
    create_source_document,
    get_source_document,
)


def test_create_source_document():
    """정책자료가 정상적으로 저장되는지 검사한다."""

    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.lastrowid = 10

    with patch(
        "app.source_repository.get_connection",
        return_value=mock_conn,
    ):
        document_id = create_source_document(
            title="정책자료 테스트",
            source_type="TEXT",
            raw_text="테스트 원문입니다.",
            organization="테스트 기관",
        )

    assert document_id == 10
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_get_source_document():
    """저장된 정책자료를 ID로 조회하는지 검사한다."""

    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value

    mock_cursor.fetchone.return_value = {
        "id": 2,
        "title": "한글 저장 테스트",
        "source_type": "TEXT",
    }

    with patch(
        "app.source_repository.get_connection",
        return_value=mock_conn,
    ):
        document = get_source_document(2)

    assert document["id"] == 2
    assert document["title"] == "한글 저장 테스트"
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


import pytest


def test_create_source_document_rollback():
    """저장 실패 시 트랜잭션을 취소하고 연결을 종료한다."""

    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = RuntimeError("DB 저장 실패")

    with patch(
        "app.source_repository.get_connection",
        return_value=mock_conn,
    ):
        with pytest.raises(RuntimeError, match="DB 저장 실패"):
            create_source_document(
                title="테스트 정책자료",
                source_type="TEXT",
                raw_text="정책자료 본문",
            )

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_invalid_title_does_not_connect():
    """잘못된 제목은 DB에 접속하기 전에 거부한다."""

    with patch("app.source_repository.get_connection") as mock_connect:
        with pytest.raises(ValueError, match="자료 제목"):
            create_source_document(
                title="   ",
                source_type="TEXT",
                raw_text="정책자료 본문",
            )

    mock_connect.assert_not_called()
