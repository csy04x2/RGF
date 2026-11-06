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

def test_review_bullets_escape_and_existing_controls():
    from collections import defaultdict
    text = '- 핵심 수치 24시간\n- <script>alert(1)</script>'
    ideas = [dict(id=i, lead_id=f'RL{i}', title='취재 제목', priority=priority,
                  angle=text if i == 1 else f'핵심 {i}', why_it_matters=text,
                  reporting_question='누가 언제 시행 여부를 확인했는가?',
                  evidence_needed=[text], review_status='검토대기',
                  reviewer=None, review_note=None)
             for i, priority in enumerate('ABC', 1)]
    html = web.PAGE.render(ideas=ideas, evidence=defaultdict(list), run_id=3,
                           source={'title': '정책', 'organization': '기관'})
    assert html.count('◎ 핵심 취재 포인트') == 3
    assert '◎ 기사 방향' not in html
    # One angle, plus three importance and three evidence fields.
    assert html.count('- 핵심 수치 24시간\n- &lt;script&gt;alert(1)&lt;/script&gt;') == 7
    assert '<script>alert(1)</script>' not in html
    assert '.info-card p,.info-card li{white-space:pre-wrap;' in html
    for priority, label in [('A', '핵심 변화·책임 확인'), ('B', '중요한 보완 취재'), ('C', '후속 확인·맥락')]:
        assert f'우선순위 {priority} · {label}' in html
    for control in ['sidebar-resizer', 'idea-list', 'class="evidence"',
                    'method="post" action="/review"', 'setPointerCapture', 'data-filter="all"']:
        assert control in html
