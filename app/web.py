from pathlib import Path
import base64
import binascii
import os
import secrets
from urllib.parse import urlsplit


from collections import defaultdict

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from jinja2 import Environment, FileSystemLoader

from .database import get_connection
from .pdf import pdf_excerpt_context
from .idea_repository import save_journalist_review
from .review import JournalistReview, update_review


app = FastAPI(title="RGF Journalist Review")


@app.middleware("http")
async def same_origin_writes(request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        def origin(value):
            try:
                parsed = urlsplit(value)
                if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
                    return None
                return (parsed.scheme, parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80))
            except ValueError:
                return None

        supplied = request.headers.get('origin') or request.headers.get('referer', '')
        expected = origin(str(request.url))
        public_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '').strip()
        if public_domain and (os.getenv('RAILWAY_PROJECT_ID') or os.getenv('RAILWAY_ENVIRONMENT_NAME')):
            # Railway terminates public HTTPS before forwarding to internal HTTP.
            # Trust server configuration, never client-supplied forwarding headers.
            expected = origin(f'https://{public_domain}')
        if (request.headers.get('sec-fetch-site') == 'cross-site'
                or origin(supplied) is None or expected is None or origin(supplied) != expected):
            return PlainTextResponse('Same-origin request required', status_code=403)
    return await call_next(request)

@app.middleware("http")
async def rgf_access_guard(request, call_next):
    """Protect all routes on Railway with one shared browser login."""
    password = os.getenv("RGF_ACCESS_PASSWORD", "")
    hosted = bool(os.getenv("RAILWAY_PROJECT_ID") or os.getenv("RAILWAY_ENVIRONMENT_NAME"))
    if not password:
        if hosted:
            return PlainTextResponse("Access password not configured", status_code=503)
        return await call_next(request)  # Preserve the existing local workflow.

    authorization = request.headers.get("authorization", "")
    valid = False
    if authorization.startswith("Basic "):
        try:
            decoded = base64.b64decode(authorization[6:], validate=True).decode("utf-8")
            username, submitted = decoded.split(":", 1)
            valid = (secrets.compare_digest(username, "rgf")
                     and secrets.compare_digest(submitted, password))
        except (binascii.Error, UnicodeDecodeError, ValueError):
            pass
    if not valid:
        return PlainTextResponse(
            "RGF requires authentication", status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="RGF"'},
        )
    return await call_next(request)


env = Environment(autoescape=True)

PAGE = env.from_string((Path(__file__).resolve().parent / "templates" / "workspace_review.html.j2").read_text(encoding="utf-8"))


def load_completed_analyses():
    """List each completed run, including repeated analyses of one document."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT ar.id AS run_id, sd.title, ar.completed_at
                   FROM analysis_runs ar
                   JOIN source_documents sd ON sd.id = ar.source_document_id
                   WHERE ar.status = 'COMPLETED'
                   ORDER BY CASE WHEN ar.completed_at IS NULL THEN 1 ELSE 0 END,
                            ar.completed_at DESC, ar.id DESC"""
            )
            return cursor.fetchall()
    finally:
        connection.close()


@app.post('/analysis-runs/{run_id}/rename')
def rename_analysis_source(run_id: int, title: str = Form(...)):
    title = title.strip()
    if run_id <= 0 or not title or len(title) > 500:
        raise HTTPException(400, '제목은 1~500자로 입력하세요.')
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT source_document_id FROM analysis_runs WHERE id = %s', (run_id,))
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(404, 'Analysis run not found')
            cursor.execute('UPDATE source_documents SET title = %s WHERE id = %s',
                           (title, row['source_document_id']))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return RedirectResponse(url=f'/workspace/{run_id}', status_code=303)


@app.post('/analysis-runs/{run_id}/delete')
def delete_analysis_run(run_id: int, confirmed: str = Form('')):
    if run_id <= 0 or confirmed != 'yes':
        raise HTTPException(400, '분석 삭제를 최종 확인해야 합니다.')
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT id FROM analysis_runs WHERE id = %s', (run_id,))
            if cursor.fetchone() is None:
                raise HTTPException(404, 'Analysis run not found')
            # FK cascades remove this run's ideas (including reviews) and links.
            # Shared source documents, source evidence, and PDFs stay intact.
            cursor.execute('DELETE FROM analysis_runs WHERE id = %s', (run_id,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    remaining = load_completed_analyses()
    target = f"/workspace/{remaining[0]['run_id']}" if remaining else '/'
    return RedirectResponse(url=target, status_code=303)


def update_working_idea(idea_id: int, *, title=None, delete=False):
    """Edit the working list only; the saved AI JSON remains unchanged."""
    if idea_id <= 0:
        raise HTTPException(400, 'Invalid idea ID')
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT analysis_run_id FROM article_ideas WHERE id = %s', (idea_id,))
            row = cursor.fetchone()
            if row is None:
                raise HTTPException(404, 'Idea not found')
            if delete:
                # Only this idea's evidence links cascade; shared evidence stays.
                cursor.execute('DELETE FROM article_ideas WHERE id = %s', (idea_id,))
            else:
                cursor.execute('UPDATE article_ideas SET title = %s WHERE id = %s', (title, idea_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return RedirectResponse(url=f"/review?run_id={row['analysis_run_id']}", status_code=303)


@app.post('/ideas/{idea_id}/rename')
def rename_working_idea(idea_id: int, title: str = Form(...)):
    title = title.strip()
    if not title or len(title) > 500:
        raise HTTPException(400, '제목은 1~500자로 입력하세요.')
    return update_working_idea(idea_id, title=title)


@app.post('/ideas/{idea_id}/delete')
def delete_working_idea(idea_id: int, confirmed: str = Form('')):
    if confirmed != 'yes':
        raise HTTPException(400, '아이디어 삭제를 최종 확인해야 합니다.')
    return update_working_idea(idea_id, delete=True)


def load_review_data(run_id: int):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, lead_id, title, angle, why_it_matters,
                       priority, review_status, reviewer, review_note
                FROM article_ideas
                WHERE analysis_run_id = %s
                ORDER BY id
                """,
                (run_id,),
            )
            ideas = cursor.fetchall()

            cursor.execute(
                """
                SELECT ae.article_idea_id, ae.relation_type,
                       ae.explanation, se.location_label, se.content
                FROM article_evidence ae
                JOIN source_evidence se
                    ON ae.source_evidence_id = se.id
                JOIN article_ideas ai
                    ON ae.article_idea_id = ai.id
                WHERE ai.analysis_run_id = %s
                ORDER BY ae.article_idea_id, se.id
                """,
                (run_id,),
            )
            evidence_rows = cursor.fetchall()

            # Reuse the analysis JSON already saved by the existing pipeline.
            cursor.execute(
                "SELECT analysis_json FROM analysis_runs WHERE id = %s AND status = 'COMPLETED'",
                (run_id,),
            )
            analysis_row = cursor.fetchone()
            cursor.execute(
                """SELECT sd.title, sd.organization, sd.raw_text FROM analysis_runs ar
                   JOIN source_documents sd ON sd.id = ar.source_document_id
                   WHERE ar.id = %s""",
                (run_id,),
            )
            source_row = cursor.fetchone()
    finally:
        connection.close()

    evidence = defaultdict(list)
    raw_source = (source_row or {}).get("raw_text") or ""
    for item in evidence_rows:
        item["source_context"] = pdf_excerpt_context(
            raw_source, item["location_label"], item["content"]
        )
        evidence[item["article_idea_id"]].append(item)
    if source_row:
        source_row.pop("raw_text", None)  # Do not pass full PDF text to the template.

    # Add existing reporting-lead details without changing database schema.
    if analysis_row and analysis_row.get("analysis_json") is not None:
        saved = analysis_row["analysis_json"]
        if isinstance(saved, (str, bytes)):
            analysis = ReportingAnalysis.model_validate_json(saved)
        else:
            analysis = ReportingAnalysis.model_validate(saved)
        by_lead_id = {lead.lead_id: lead for lead in analysis.reporting_leads}
        for idea in ideas:
            lead = by_lead_id.get(idea["lead_id"])
            if lead is not None:
                idea["reporting_question"] = lead.reporting_question
                idea["evidence_needed"] = lead.evidence_needed

    return ideas, evidence, (source_row or {"title": "분석 자료", "organization": None})


@app.get("/review", response_class=HTMLResponse)
def review_page(run_id: int = 1):
    if run_id <= 0:
        raise HTTPException(400, "Invalid analysis run ID")

    ideas, evidence, source = load_review_data(run_id)

    return PAGE.render(
        run_id=run_id,
        ideas=ideas,
        evidence=evidence,
        source=source,
        completed_analyses=load_completed_analyses(),
    )


@app.post("/review")
def submit_review(
    run_id: int = Form(...),
    lead_id: str = Form(...),
    reviewer: str = Form(...),
    status: str = Form(...),
    review_note: str = Form(""),
):
    if run_id <= 0:
        raise HTTPException(400, "Invalid analysis run ID")

    reviewer = reviewer.strip()
    if not reviewer:
        raise HTTPException(400, "기자 이름을 입력해야 합니다.")

    if status not in ("검토대기", "승인", "보류"):
        raise HTTPException(400, "올바르지 않은 검토 상태입니다.")

    if status == "보류" and not review_note.strip():
        raise HTTPException(400, "보류 사유를 입력해야 합니다.")

    review = update_review(
        JournalistReview(
            lead_id=lead_id,
            reviewer=reviewer,
        ),
        status=status,
        review_note=review_note,
    )

    try:
        save_journalist_review(run_id, review)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    return RedirectResponse(
        url=f"/review?run_id={run_id}&lead={lead_id}",
        status_code=303,
    )


from pathlib import Path
from uuid import uuid4

from fastapi import File, UploadFile
from .source_service import register_pdf
from .analysis_repository import save_analysis_run
from .idea_repository import save_article_idea
from .llm import OpenAIJSONClient
from .pipeline import Pipeline
from fastapi import BackgroundTasks
from .analysis_jobs import create_pending_run, run_analysis_job
from .pdf import extract_pdf, locate_pdf_excerpt_segments
from .source_repository import save_source_evidence
from .idea_repository import link_article_evidence


UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@app.get("/", response_class=HTMLResponse)
def upload_page():
    return (Path(__file__).resolve().parent / "templates" / "workspace_upload.html").read_text(encoding="utf-8")

@app.post("/analyze")
def analyze_pdf(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    organization: str = Form(""),
    file: UploadFile = File(...),
):
    title = title.strip()
    organization = organization.strip()
    if not title:
        raise HTTPException(400, "정책자료 제목을 입력해야 합니다.")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "PDF 파일만 업로드할 수 있습니다.")

    try:
        data = file.file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        file.file.close()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "PDF 파일은 10MB 이하여야 합니다.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(400, "올바른 PDF 파일이 아닙니다.")

    # Validate configuration before registering the job; no AI request here.
    model_name = OpenAIJSONClient().model
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = UPLOAD_DIR / f"{uuid4().hex}.pdf"
    pdf_path.write_bytes(data)
    try:
        source_id = register_pdf(
            file_path=pdf_path,
            title=title,
            organization=organization or None,
        )
        run_id = create_pending_run(source_id, model_name)
    except Exception:
        # A registered document may remain if creating its run fails.
        # Keep its PDF for inspection; do not silently delete it.
        raise

    background_tasks.add_task(run_analysis_job, run_id, source_id, str(pdf_path))
    return RedirectResponse(url=f"/analysis-status/{run_id}", status_code=303)


@app.get("/analysis-status/{run_id}", response_class=HTMLResponse)
def analysis_status_page(run_id: int):
    if run_id <= 0:
        raise HTTPException(400, "Invalid analysis run ID")
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status, created_at FROM analysis_runs WHERE id = %s",
                (run_id,),
            )
            job = cursor.fetchone()
    finally:
        connection.close()
    if job is None:
        raise HTTPException(404, "Analysis run not found")
    if job["status"] == "COMPLETED":
        return RedirectResponse(url=f"/workspace/{run_id}", status_code=303)

    import html
    status = job["status"]
    message = (
        "분석 중입니다. 이 화면은 자동으로 갱신됩니다. 다시 분석 버튼을 누르지 마세요."
        if status in ("PENDING", "RUNNING")
        else "분석이 완료되지 않았습니다. 관리자에게 Railway 로그 확인을 요청하세요."
    )
    refresh = '<meta http-equiv="refresh" content="5">' if status in ("PENDING", "RUNNING") else ''
    return HTMLResponse(
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        + refresh
        + '<meta name="viewport" content="width=device-width,initial-scale=1">'
        + '<title>RGF · 분석 진행 상태</title>'
        + '<style>body{background:#f7f1eb;font-family:system-ui,sans-serif;color:#2b2521;'
        + 'margin:10vh auto;padding:24px;max-width:640px}main{background:white;'
        + 'border:1px solid #eadbd0;border-radius:14px;padding:28px}h1{font-size:24px}'
        + 'p{line-height:1.8}a{color:#bd541b}</style></head><body><main>'
        + '<h1>RGF · 분석 진행 상태</h1>'
        + f'<p>분석 #{run_id} · {html.escape(status)}</p>'
        + '<p>' + html.escape(message) + '</p>'
        + '<p><a href="/">새 자료 분석 화면</a></p></main></body></html>'
    )

from .models import ReportingAnalysis
from .renderer import render


@app.get("/analysis/{run_id}", response_class=HTMLResponse)
def analysis_detail(run_id: int):
    """Display the complete saved AI analysis."""

    if run_id <= 0:
        raise HTTPException(400, "Invalid analysis run ID")

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT analysis_json
                FROM analysis_runs
                WHERE id = %s
                  AND status = 'COMPLETED'
                """,
                (run_id,),
            )
            row = cursor.fetchone()
    finally:
        connection.close()

    if row is None or row["analysis_json"] is None:
        raise HTTPException(
            404,
            "Completed analysis not found",
        )

    saved = row["analysis_json"]

    if isinstance(saved, (str, bytes)):
        analysis = ReportingAnalysis.model_validate_json(saved)
    else:
        analysis = ReportingAnalysis.model_validate(saved)

    html = render(analysis)

    navigation = (
        '<nav style="padding:16px;'
        'border-bottom:1px solid #ddd">'
        f'<a href="/review?run_id={run_id}">'
        'Return to journalist review</a>'
        '</nav>'
    )

    return HTMLResponse(
        content=html.replace("<body>", "<body>" + navigation, 1)
    )


@app.get("/workspace/{run_id}", response_class=HTMLResponse)
def workspace_overview(run_id: int):
    if run_id <= 0:
        raise HTTPException(400, "Invalid analysis run ID")
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT sd.title, sd.organization, ar.completed_at,
                          ar.analysis_json, ar.structured_source_json
                   FROM analysis_runs ar
                   JOIN source_documents sd ON sd.id = ar.source_document_id
                   WHERE ar.id = %s AND ar.status = 'COMPLETED'""",
                (run_id,),
            )
            record = cursor.fetchone()
            cursor.execute(
                "SELECT COUNT(*) AS total FROM article_ideas WHERE analysis_run_id = %s",
                (run_id,),
            )
            count = cursor.fetchone()
            cursor.execute(
                "SELECT id, lead_id, title, review_status FROM article_ideas WHERE analysis_run_id = %s ORDER BY id",
                (run_id,),
            )
            nav_ideas = cursor.fetchall()
    finally:
        connection.close()
    if not record or record['analysis_json'] is None:
        raise HTTPException(404, "Completed analysis not found")
    saved = record['analysis_json']
    analysis = (ReportingAnalysis.model_validate_json(saved)
                if isinstance(saved, (str, bytes))
                else ReportingAnalysis.model_validate(saved))
    from .models import SourceStructure
    raw = record['structured_source_json']
    structured = ((SourceStructure.model_validate_json(raw)
                   if isinstance(raw, (str, bytes))
                   else SourceStructure.model_validate(raw))
                  if raw is not None else None)
    overview_env = Environment(
        loader=FileSystemLoader(Path(__file__).resolve().parent / 'templates'),
        autoescape=True,
    )
    return overview_env.get_template('workspace_overview.html.j2').render(
        source=record, run_id=run_id, analysis=analysis,
        idea_count=count['total'] if count else 0, nav_ideas=nav_ideas,
        changes=analysis.material_changes,
        gaps=structured.source_gaps if structured else [],
        completed_analyses=load_completed_analyses(),
    )
