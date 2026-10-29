
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
