
from unittest.mock import MagicMock, patch

import pytest

from app.analysis_repository import save_analysis_run
from app.models import ReportingAnalysis, SourceStructure
from tests.test_core import analysis_data, source_data


def make_analysis():
    return ReportingAnalysis.model_validate(analysis_data())


def make_structure():
    return SourceStructure.model_validate(source_data())


def test_save_analysis_run_success():
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.lastrowid = 123

    with patch(
        "app.analysis_repository.get_connection",
        return_value=connection,
    ):
        run_id = save_analysis_run(
            source_document_id=1,
            structured=make_structure(),
            analysis=make_analysis(),
            model_name="test-model",
            prompt_version="v0.1",
        )

    assert run_id == 123
    cursor.execute.assert_called_once()
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once()


def test_save_analysis_run_rollback():
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = RuntimeError("DB 저장 실패")

    with patch(
        "app.analysis_repository.get_connection",
        return_value=connection,
    ):
        with pytest.raises(RuntimeError, match="DB 저장 실패"):
            save_analysis_run(
                source_document_id=1,
                structured=make_structure(),
                analysis=make_analysis(),
                model_name="test-model",
                prompt_version="v0.1",
            )

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()


def test_invalid_source_id_does_not_connect():
    with patch("app.analysis_repository.get_connection") as connect:
        with pytest.raises(ValueError, match="정책자료 ID"):
            save_analysis_run(
                source_document_id=0,
                structured=make_structure(),
                analysis=make_analysis(),
                model_name="test-model",
                prompt_version="v0.1",
            )

    connect.assert_not_called()


def test_save_analysis_run_without_structure():
    """1차 구조화 결과가 없어도 최종 분석을 저장할 수 있다."""

    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.lastrowid = 456

    with patch(
        "app.analysis_repository.get_connection",
        return_value=connection,
    ):
        run_id = save_analysis_run(
            source_document_id=1,
            structured=None,
            analysis=make_analysis(),
            model_name="test-model",
            prompt_version="v0.1",
        )

    assert run_id == 456

    # MySQL에 전달되는 값 확인
    cursor.execute.assert_called_once()
    sql, values = cursor.execute.call_args.args

    assert "structured_source_json" in sql
    assert values[3] is None
    assert values[4] is not None

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once()
