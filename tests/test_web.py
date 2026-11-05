from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app import web


def test_web_pdf_analysis_flow(monkeypatch, tmp_path):
    """Upload creates a pending run and queues analysis; it does not run inline."""
    client = MagicMock()
    client.model = "test-model"

    register = MagicMock(return_value=3)
    pending = MagicMock(return_value=10)
    queued = MagicMock()

    monkeypatch.setattr(web, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(web, "OpenAIJSONClient", lambda: client)
    monkeypatch.setattr(web, "register_pdf", register)
    monkeypatch.setattr(web, "create_pending_run", pending)
    # TestClient executes BackgroundTasks before returning, so prevent a real
    # PDF parse / OpenAI call and assert that the task was scheduled instead.
    monkeypatch.setattr(web.BackgroundTasks, "add_task", queued)

    response = TestClient(web.app).post(
        "/analyze",
        data={
            "title": "Test policy document",
            "organization": "Test ministry",
        },
        files={
            "file": ("test.pdf", b"%PDF-1.4\n%test", "application/pdf"),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/analysis-status/10"
    register.assert_called_once()
    assert register.call_args.kwargs["title"] == "Test policy document"
    pending.assert_called_once_with(3, "test-model")
    queued.assert_called_once()
    args = queued.call_args.args
    assert args[0] is web.run_analysis_job
    assert args[1:3] == (10, 3)
    assert Path(args[3]).is_file()
