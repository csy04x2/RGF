
import pytest

from app import idea_repository
from tests.test_core import analysis_data
from app.models import ReportingAnalysis


class FakeCursor:
    lastrowid = 123

    def __init__(self, fail=False):
        self.fail = fail

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, values):
        if self.fail:
            raise RuntimeError("DB 저장 실패")


class FakeConnection:
    def __init__(self, fail=False):
        self.fail = fail
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return FakeCursor(self.fail)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def make_analysis():
    return ReportingAnalysis.model_validate(analysis_data())


def test_save_article_idea_success(monkeypatch):
    connection = FakeConnection()

    monkeypatch.setattr(
        idea_repository,
        "get_connection",
        lambda: connection,
    )

    saved_id = idea_repository.save_article_idea(
        make_analysis(),
        analysis_run_id=1,
        lead_id="RL1",
    )

    assert saved_id == 123
    assert connection.committed
    assert not connection.rolled_back
    assert connection.closed


def test_save_article_idea_rollback(monkeypatch):
    connection = FakeConnection(fail=True)

    monkeypatch.setattr(
        idea_repository,
        "get_connection",
        lambda: connection,
    )

    with pytest.raises(RuntimeError, match="DB 저장 실패"):
        idea_repository.save_article_idea(
            make_analysis(),
            analysis_run_id=1,
            lead_id="RL1",
        )

    assert not connection.committed
    assert connection.rolled_back
    assert connection.closed


def test_invalid_lead_does_not_connect(monkeypatch):
    def unexpected_connection():
        raise AssertionError("DB에 연결하면 안 됩니다.")

    monkeypatch.setattr(
        idea_repository,
        "get_connection",
        unexpected_connection,
    )

    with pytest.raises(
        ValueError,
        match="존재하지 않는 취재 아이디어",
    ):
        idea_repository.save_article_idea(
            make_analysis(),
            analysis_run_id=1,
            lead_id="RL999",
        )


from unittest.mock import MagicMock

from app.review import JournalistReview, update_review


def make_approved_review():
    review = JournalistReview(
        lead_id="RL7",
        reviewer="테스트 기자",
    )
    return update_review(
        review,
        status="승인",
        review_note="원문 근거 확인 완료",
    )


def test_save_journalist_review_success(monkeypatch):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.rowcount = 1

    monkeypatch.setattr(
        idea_repository,
        "get_connection",
        lambda: connection,
    )

    idea_repository.save_journalist_review(
        analysis_run_id=1,
        review=make_approved_review(),
    )

    cursor.execute.assert_called_once()
    sql, values = cursor.execute.call_args.args

    assert "UPDATE article_ideas" in sql
    assert "analysis_run_id = %s" in sql
    assert "lead_id = %s" in sql
    assert values[0] == "승인"
    assert values[4] == 1
    assert values[5] == "RL7"

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once()


def test_save_journalist_review_missing_target(monkeypatch):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.rowcount = 0
    cursor.fetchone.return_value = None

    monkeypatch.setattr(
        idea_repository,
        "get_connection",
        lambda: connection,
    )

    with pytest.raises(ValueError, match="검토 대상"):
        idea_repository.save_journalist_review(
            analysis_run_id=1,
            review=make_approved_review(),
        )

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()


def test_save_journalist_review_db_error(monkeypatch):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = RuntimeError("DB 오류")

    monkeypatch.setattr(
        idea_repository,
        "get_connection",
        lambda: connection,
    )

    with pytest.raises(RuntimeError, match="DB 오류"):
        idea_repository.save_journalist_review(
            analysis_run_id=1,
            review=make_approved_review(),
        )

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()


def test_save_journalist_review_same_values_again(monkeypatch):
    """An existing review should allow saving identical values again."""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value

    # MySQL can return zero when UPDATE changes no values.
    cursor.rowcount = 0
    cursor.fetchone.return_value = {"id": 7}

    monkeypatch.setattr(
        idea_repository,
        "get_connection",
        lambda: connection,
    )

    idea_repository.save_journalist_review(
        analysis_run_id=1,
        review=make_approved_review(),
    )

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once()
