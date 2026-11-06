from pathlib import Path
from unittest.mock import MagicMock
import pytest

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
        headers={'Origin': 'http://testserver'},
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


@pytest.fixture
def saved_runs(monkeypatch, tmp_path):
    """Execute the production read queries against isolated SQL fixtures."""
    import sqlite3
    from contextlib import contextmanager
    from datetime import datetime
    from tests.test_core import analysis_data
    from app.models import ReportingAnalysis

    path = tmp_path / 'navigation.sqlite'
    analysis = ReportingAnalysis.model_validate(analysis_data()).model_dump_json()
    with sqlite3.connect(path) as db:
        db.executescript('''
            CREATE TABLE source_documents (id INTEGER PRIMARY KEY, title TEXT,
                organization TEXT, raw_text TEXT);
            PRAGMA foreign_keys = ON;
            CREATE TABLE analysis_runs (id INTEGER PRIMARY KEY, source_document_id INTEGER REFERENCES source_documents(id) ON DELETE CASCADE,
                status TEXT, completed_at TEXT, analysis_json TEXT, structured_source_json TEXT);
            CREATE TABLE article_ideas (id INTEGER PRIMARY KEY, analysis_run_id INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
                lead_id TEXT, title TEXT, angle TEXT, why_it_matters TEXT, priority TEXT,
                review_status TEXT, reviewer TEXT, review_note TEXT);
            CREATE TABLE source_evidence (id INTEGER PRIMARY KEY, location_label TEXT, content TEXT);
            CREATE TABLE article_evidence (article_idea_id INTEGER REFERENCES article_ideas(id) ON DELETE CASCADE, source_evidence_id INTEGER REFERENCES source_evidence(id) ON DELETE CASCADE,
                relation_type TEXT, explanation TEXT);
        ''')
        db.execute('INSERT INTO source_documents VALUES (1, ?, ?, ?)',
                   ('동일 보도자료 <script>제목</script>', '기관', '원문'))
        for run_id, status, date in [
            (2, 'COMPLETED', '2026-11-04'), (3, 'FAILED', '2026-11-05'),
            (4, 'COMPLETED', '2026-11-06'), (5, 'PENDING', None),
            (6, 'RUNNING', None),
        ]:
            db.execute('INSERT INTO analysis_runs VALUES (?, 1, ?, ?, ?, NULL)',
                       (run_id, status, date, analysis))
            db.execute('INSERT INTO article_ideas VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)',
                       (run_id, run_id, 'RL1', f'run-{run_id}-only-idea',
                        '방향', '가치', 'A', '승인' if run_id == 2 else '검토대기'))
        db.execute("UPDATE article_ideas SET reviewer = '기자', review_note = '검토 메모'")
        db.execute("INSERT INTO source_evidence VALUES (1, 'PDF 1쪽', '공유 근거')")
        for run_id in [2, 4]:
            db.execute("INSERT INTO article_evidence VALUES (?, 1, 'CONTEXT', '문맥')", (run_id,))

    queries = []

    class Connection:
        def __init__(self):
            self.db = sqlite3.connect(path)
            self.db.execute('PRAGMA foreign_keys = ON')
            self.db.row_factory = self.row

        @staticmethod
        def row(cursor, values):
            result = dict(zip([col[0] for col in cursor.description], values))
            if result.get('completed_at'):
                result['completed_at'] = datetime.fromisoformat(result['completed_at'])
            return result

        @contextmanager
        def cursor(self):
            cursor = self.db.cursor()

            class Cursor:
                def execute(self, sql, params=()):
                    queries.append((sql, params))
                    return cursor.execute(sql.replace('%s', '?'), params)

                def fetchall(self):
                    return cursor.fetchall()

                def fetchone(self):
                    return cursor.fetchone()

            try:
                yield Cursor()
            finally:
                cursor.close()

        def close(self):
            self.db.close()

        def commit(self):
            self.db.commit()

        def rollback(self):
            self.db.rollback()

    monkeypatch.setattr(web, 'get_connection', Connection)
    return queries


def test_completed_analysis_list_filters_and_orders_runs(saved_runs):
    rows = web.load_completed_analyses()
    assert [row['run_id'] for row in rows] == [4, 2]
    assert rows[0]['title'] == rows[1]['title']
    assert all(sql.lstrip().startswith('SELECT') for sql, _ in saved_runs)


@pytest.mark.parametrize('run_id', [2, 4])
@pytest.mark.parametrize('page', ['overview', 'review'])
def test_saved_analysis_switching_keeps_run_scoped_ideas(saved_runs, run_id, page):
    html = web.workspace_overview(run_id) if page == 'overview' else web.review_page(run_id)
    other = 4 if run_id == 2 else 2
    assert '보도자료</summary>' in html
    assert html.index('분석 #4 · 2026.11.06') < html.index('분석 #2 · 2026.11.04')
    assert f'class="analysis-link selected" href="/workspace/{run_id}" aria-current="true"' in html
    assert f'class="analysis-link" href="/workspace/{other}"' in html
    for excluded in [3, 5, 6]:
        assert f'href="/workspace/{excluded}"' not in html
    assert '동일 보도자료 &lt;script&gt;제목&lt;/script&gt;' in html
    assert '<script>제목</script>' not in html
    assert f'run-{run_id}-only-idea' in html
    assert f'run-{other}-only-idea' not in html
    assert f'/review?run_id={run_id}&amp;lead=RL1' in html
    assert f'href="/workspace/{run_id}"' in html
    assert 'sidebar-resizer' in html and 'setPointerCapture' in html
    assert '.lead-label{white-space:normal;' in html
    if page == 'review':
        assert 'value="승인" selected' in html if run_id == 2 else 'value="검토대기" selected' in html
    # Both overview and review queries bind the selected run ID.
    scoped = [(sql, params) for sql, params in saved_runs if 'analysis_run_id = %s' in sql]
    assert scoped and all(params == (run_id,) for _, params in scoped)


def test_completed_analysis_connection_closed_on_error(monkeypatch):
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value.execute.side_effect = RuntimeError('DB unavailable')
    monkeypatch.setattr(web, 'get_connection', lambda: connection)
    with pytest.raises(RuntimeError, match='DB unavailable'):
        web.load_completed_analyses()
    connection.close.assert_called_once()


def management_snapshot():
    connection = web.get_connection()
    try:
        with connection.cursor() as cursor:
            result = {}
            for table in ['source_documents', 'analysis_runs', 'article_ideas', 'source_evidence', 'article_evidence']:
                cursor.execute(f'SELECT * FROM {table}')
                result[table] = cursor.fetchall()
            return result
    finally:
        connection.close()


@pytest.fixture
def management_client(saved_runs, monkeypatch):
    monkeypatch.setenv('RGF_ACCESS_PASSWORD', 'test-password')
    client = TestClient(web.app, headers={'Origin': 'http://testserver'}, follow_redirects=False)
    client.auth = ('rgf', 'test-password')
    return client


def test_rename_shared_source_only_updates_title(management_client):
    before = management_snapshot()
    response = management_client.post('/analysis-runs/2/rename', data={'title': '  새 제목 <b>정책</b>  '})
    assert response.status_code == 303
    assert response.headers['location'] == '/workspace/2'
    after = management_snapshot()
    before['source_documents'][0]['title'] = '새 제목 <b>정책</b>'
    assert after == before
    for run_id in [2, 4]:
        for url in [f'/workspace/{run_id}', f'/review?run_id={run_id}']:
            html = management_client.get(url).text
            assert '<h1>새 제목 &lt;b&gt;정책&lt;/b&gt;</h1>' in html
            assert 'value="새 제목 &lt;b&gt;정책&lt;/b&gt;"' in html
            assert '같은 보도자료의 모든 분석에 제목 변경이 적용됩니다.' in html


@pytest.mark.parametrize('title', [' ', 'x' * 501])
def test_invalid_rename_is_unchanged(management_client, title):
    before = management_snapshot()
    assert management_client.post('/analysis-runs/2/rename', data={'title': title}).status_code == 400
    assert management_snapshot() == before


def test_delete_one_run_preserves_other_reviews_and_shared_data(management_client, tmp_path):
    pdf = tmp_path / 'original.pdf'
    pdf.write_bytes(b'%PDF-test')
    before = management_snapshot()
    response = management_client.post('/analysis-runs/2/delete', data={'confirmed': 'yes'})
    assert response.status_code == 303 and response.headers['location'] == '/workspace/4'
    after = management_snapshot()
    expected = dict(before)
    expected['analysis_runs'] = [r for r in before['analysis_runs'] if r['id'] != 2]
    expected['article_ideas'] = [r for r in before['article_ideas'] if r['analysis_run_id'] != 2]
    expected['article_evidence'] = [r for r in before['article_evidence'] if r['article_idea_id'] != 2]
    assert after == expected
    assert pdf.read_bytes() == b'%PDF-test'
    assert management_client.post('/analysis-runs/4/delete', data={'confirmed': 'yes'}).headers['location'] == '/'


def test_delete_cancel_and_get_do_not_write(management_client):
    before = management_snapshot()
    for data in [{}, {'confirmed': 'no'}]:
        assert management_client.post('/analysis-runs/2/delete', data=data).status_code == 400
    for action in ['delete', 'rename']:
        assert management_client.get(f'/analysis-runs/2/{action}').status_code == 405
    for url in ['/workspace/2', '/review?run_id=2']:
        html = management_client.get(url).text
        assert 'onsubmit="return confirm(' in html
        assert '연결된 취재 아이디어와 기자 검토 기록도 삭제됩니다.' in html
        assert 'name="confirmed" value="yes"' in html
    assert management_snapshot() == before


@pytest.mark.parametrize('headers', [
    {'Origin': 'https://evil.example'}, {'Origin': 'null'},
    {'Referer': 'http://testserver.evil.example/page'}, {},
    {'Origin': 'http://testserver', 'Sec-Fetch-Site': 'cross-site'},
])
def test_management_rejects_foreign_or_missing_origin(management_client, headers):
    before = management_snapshot()
    # Use a fresh client to omit the fixture's default Origin header.
    client = TestClient(web.app)
    client.auth = ('rgf', 'test-password')
    for action, data in [('rename', {'title': 'forged'}), ('delete', {'confirmed': 'yes'})]:
        assert client.post(f'/analysis-runs/2/{action}', data=data, headers=headers).status_code == 403
    assert management_snapshot() == before


def test_management_auth_and_same_origin_referer(management_client):
    before = management_snapshot()
    client = TestClient(web.app, headers={'Origin': 'http://testserver'})
    assert client.post('/analysis-runs/2/delete', data={'confirmed': 'yes'}).status_code == 401
    assert management_snapshot() == before
    client = TestClient(web.app, follow_redirects=False)
    client.auth = ('rgf', 'test-password')
    response = client.post('/analysis-runs/2/rename', data={'title': '참조 헤더'},
                           headers={'Referer': 'http://testserver/workspace/2'})
    assert response.status_code == 303


@pytest.mark.parametrize('action,data', [('rename', {'title': '새 제목'}), ('delete', {'confirmed': 'yes'})])
def test_management_missing_run_does_not_write(management_client, action, data):
    before = management_snapshot()
    assert management_client.post(f'/analysis-runs/999/{action}', data=data).status_code == 404
    assert management_snapshot() == before


@pytest.mark.parametrize('action', ['rename', 'delete'])
def test_management_write_failure_rolls_back_and_closes(monkeypatch, action):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = {'id': 2, 'source_document_id': 1}
    cursor.execute.side_effect = [None, RuntimeError('write failed')]
    monkeypatch.setattr(web, 'get_connection', lambda: connection)
    with pytest.raises(RuntimeError, match='write failed'):
        if action == 'rename':
            web.rename_analysis_source(2, '새 제목')
        else:
            web.delete_analysis_run(2, 'yes')
    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()


def test_idea_rename_changes_only_working_title(management_client):
    before = management_snapshot()
    response = management_client.post('/ideas/2/rename', data={'title': '  새 아이디어 <b>제목</b>  '})
    assert response.status_code == 303
    assert response.headers['location'] == '/review?run_id=2'
    next(r for r in before['article_ideas'] if r['id'] == 2)['title'] = '새 아이디어 <b>제목</b>'
    assert management_snapshot() == before
    for url in ['/review?run_id=2', '/workspace/2']:
        html = management_client.get(url).text
        assert '새 아이디어 &lt;b&gt;제목&lt;/b&gt;' in html
        assert '<b>제목</b>' not in html


def test_idea_delete_preserves_run_other_ideas_and_json(management_client):
    connection = web.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('''INSERT INTO article_ideas
                SELECT 20, analysis_run_id, 'RL2', 'surviving-same-run-idea', angle,
                       why_it_matters, priority, review_status, reviewer, review_note
                FROM article_ideas WHERE id = 2''')
            cursor.execute("INSERT INTO article_evidence VALUES (20, 1, 'CONTEXT', '공유 링크')")
        connection.commit()
    finally:
        connection.close()
    before = management_snapshot()
    response = management_client.post('/ideas/2/delete', data={'confirmed': 'yes'})
    assert response.status_code == 303 and response.headers['location'] == '/review?run_id=2'
    expected = dict(before)
    expected['article_ideas'] = [r for r in before['article_ideas'] if r['id'] != 2]
    expected['article_evidence'] = [r for r in before['article_evidence'] if r['article_idea_id'] != 2]
    assert management_snapshot() == expected
    # Repeated fresh renders must read the working DB list, never rebuild from JSON.
    for _ in range(2):
        for url in ['/review?run_id=2', '/workspace/2']:
            html = management_client.get(url).text
            assert 'run-2-only-idea' not in html
            assert 'surviving-same-run-idea' in html
        assert '취재 아이디어 1건' in management_client.get('/review?run_id=2').text
        assert '<strong>1</strong><span class="muted">취재 아이디어</span>' in management_client.get('/workspace/2').text
    management_client.post('/ideas/20/delete', data={'confirmed': 'yes'})
    assert '취재 아이디어 0건' in management_client.get('/review?run_id=2').text
    assert '<strong>0</strong><span class="muted">취재 아이디어</span>' in management_client.get('/workspace/2').text


def test_idea_management_guards_and_cancel(management_client):
    before = management_snapshot()
    for title in [' ', 'x' * 501]:
        assert management_client.post('/ideas/2/rename', data={'title': title}).status_code == 400
    for data in [{}, {'confirmed': 'no'}]:
        assert management_client.post('/ideas/2/delete', data=data).status_code == 400
    for action, data in [('rename', {'title': '새 제목'}), ('delete', {'confirmed': 'yes'})]:
        assert management_client.get(f'/ideas/2/{action}').status_code == 405
        assert management_client.post(f'/ideas/999/{action}', data=data).status_code == 404
        assert management_client.post(f'/ideas/2/{action}', data=data,
                                      headers={'Origin': 'https://evil.example'}).status_code == 403
        anonymous = TestClient(web.app, headers={'Origin': 'http://testserver'})
        assert anonymous.post(f'/ideas/2/{action}', data=data).status_code == 401
    assert management_snapshot() == before


@pytest.mark.parametrize('page', ['overview', 'review'])
def test_common_management_ui_structure(management_client, page):
    from html.parser import HTMLParser

    class Controls(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.actions = 0

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'details' and attrs.get('class') == 'run-actions':
                assert not any(parent in ('a', 'button') for parent in self.stack)
                self.actions += 1
            if tag not in ('input', 'meta', 'link', 'br', 'hr'):
                self.stack.append(tag)

        def handle_endtag(self, tag):
            assert self.stack and self.stack.pop() == tag

    html = management_client.get('/workspace/2' if page == 'overview' else '/review?run_id=2').text
    controls = Controls()
    controls.feed(html)
    assert controls.actions == (3 if page == 'overview' else 4)
    for rule in ['.managed-row:hover,.managed-row:focus-within{background:#f3e1d3}',
                 '.managed-row>.run-actions>summary{opacity:0;',
                 '@media(hover:none),(pointer:coarse),(max-width:650px)',
                 '.managed-row:has(>a.selected)', "event.key==='Escape'",
                 '연결된 기자 검토 기록과 원문 근거 링크가 작업 목록에서 사라집니다.',
                 'action="/ideas/2/rename"', 'action="/ideas/2/delete"']:
        assert rule in html
    if page == 'review':
        assert "b.closest('.managed-row').hidden=b.hidden" in html


@pytest.mark.parametrize('delete', [True, False])
def test_idea_management_failure_rolls_back(monkeypatch, delete):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = {'analysis_run_id': 2}
    cursor.execute.side_effect = [None, RuntimeError('write failed')]
    monkeypatch.setattr(web, 'get_connection', lambda: connection)
    with pytest.raises(RuntimeError, match='write failed'):
        web.update_working_idea(2, title='새 제목', delete=delete)
    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()


def test_upload_sidebar_uses_completed_runs_without_mixing_ideas(management_client, saved_runs):
    from html.parser import HTMLParser

    class Groups(HTMLParser):
        groups = 0

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'details' and attrs.get('class') == 'lead-group':
                assert 'open' not in attrs
                self.groups += 1

    response = management_client.get('/')
    assert response.status_code == 200
    html = response.text
    parser = Groups()
    parser.feed(html)
    assert parser.groups == 2
    assert '▤ 자료 등록' not in html
    assert '보도자료를 먼저 선택해 취재 아이디어를 확인하세요.' in html
    assert '취재 아이디어</summary>' in html
    assert html.index('분석 #4 ·') < html.index('분석 #2 ·')
    for run_id in [2, 4]:
        assert f'href="/workspace/{run_id}"' in html
        assert f'action="/analysis-runs/{run_id}/rename"' in html
        assert f'action="/analysis-runs/{run_id}/delete"' in html
    for run_id in [3, 5, 6]:
        assert f'href="/workspace/{run_id}"' not in html
    assert '동일 보도자료 &lt;script&gt;제목&lt;/script&gt;' in html
    assert '<script>제목</script>' not in html
    assert 'only-idea' not in html and '/ideas/' not in html
    assert not any('article_ideas' in sql for sql, _ in saved_runs)
    for control in ['.managed-row:hover,.managed-row:focus-within{background:#f3e1d3}',
                    '.lead-label{white-space:normal;', 'popover="manual"',
                    '✎ 이름 변경', 'return confirm(', 'panel.showPopover()',
                    'sidebar-resizer', 'setPointerCapture', 'rgf_sidebar_width',
                    "event.key!=='ArrowLeft'", "event.key==='Escape'"]:
        assert control in html
    assert 'method="post" action="/analyze" enctype="multipart/form-data" id="analyze-form"' in html
    assert 'accept=".pdf,application/pdf" required' in html
    assert "button.disabled=true" in html


def test_upload_empty_analysis_list_reuses_loader(monkeypatch):
    loader = MagicMock(return_value=[])
    monkeypatch.setattr(web, 'load_completed_analyses', loader)
    html = web.upload_page()
    loader.assert_called_once_with()
    assert '완료된 분석이 없습니다.' in html
    assert '보도자료를 먼저 선택' in html
    assert 'action="/analyze"' in html


def test_upload_sidebar_retains_existing_workspace_scripts():
    templates = Path(web.__file__).parent / 'templates'
    overview = (templates / 'workspace_overview.html.j2').read_text(encoding='utf-8')
    upload = (templates / 'workspace_upload.html').read_text(encoding='utf-8')
    # Reuse the established resizer and management interactions unchanged.
    scripts = overview[overview.index('<script>'):overview.rindex('</script>') + len('</script>')]
    assert scripts in upload
