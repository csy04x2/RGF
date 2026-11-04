
from collections import defaultdict

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment

from .database import get_connection
from .idea_repository import save_journalist_review
from .review import JournalistReview, update_review


app = FastAPI(title="RGF Journalist Review")

env = Environment(autoescape=True)

PAGE = env.from_string("""
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>RGF 기자 검토</title>
<style>
body {
    font-family: system-ui, sans-serif;
    max-width: 900px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.6;
    color: #222;
}
article {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 24px;
    margin: 24px 0;
}
h1 { margin-bottom: 4px; }
h2 { margin-bottom: 8px; }
small, .muted { color: #666; }
.evidence {
    background: #f5f5f5;
    padding: 12px;
    margin: 8px 0;
    border-radius: 6px;
    white-space: pre-wrap;
}
label {
    display: block;
    margin: 12px 0;
}
input, select, textarea {
    width: 100%;
    box-sizing: border-box;
    padding: 9px;
    font: inherit;
}
button {
    padding: 10px 20px;
    cursor: pointer;
}
</style>
</head>
<body>
<h1>RGF 기자 검토</h1>
<p class="muted">분석 실행 ID: {{ run_id }}</p>
<p class="muted">분석 실행 ID: {{ run_id }}</p>
<p>AI가 생성한 취재 아이디어를 검토하고 승인하거나 보류합니다.</p>

{% for idea in ideas %}
<article>
    <small>{{ idea.lead_id }} · 우선순위 {{ idea.priority }}</small>
    <h2>{{ idea.title }}</h2>
    <p><strong>기사 방향:</strong> {{ idea.angle }}</p>
    <p><strong>취재 가치:</strong> {{ idea.why_it_matters }}</p>

    <h3>원문 근거</h3>
    {% if evidence[idea.id] %}
        {% for item in evidence[idea.id] %}
        <div class="evidence">
            <strong>{{ item.location_label }}
            · {{ item.relation_type }}</strong>
            <p>{{ item.content }}</p>
            <small>{{ item.explanation }}</small>
        </div>
        {% endfor %}
    {% else %}
        <p class="muted">
            아직 DB에 연결된 원문 근거가 없습니다.
            근거 미확인 상태로 검토해야 합니다.
        </p>
    {% endif %}

    <h3>기자 검토</h3>
    <p>현재 상태: <strong>{{ idea.review_status }}</strong></p>

    <form method="post" action="/review">
        <input type="hidden" name="run_id" value="{{ run_id }}">
        <input type="hidden" name="lead_id" value="{{ idea.lead_id }}">

        <label>기자 이름
            <input name="reviewer"
                   value="{{ idea.reviewer or '' }}"
                   required maxlength="255">
        </label>

        <label>검토 결과
            <select name="status">
                {% for status in ["검토대기", "승인", "보류"] %}
                <option value="{{ status }}"
                    {% if status == idea.review_status %}selected{% endif %}>
                    {{ status }}
                </option>
                {% endfor %}
            </select>
        </label>

        <label>검토 메모
            <textarea name="review_note" rows="3">{{ idea.review_note or '' }}</textarea>
        </label>

        <button type="submit">검토 결과 저장</button>
    </form>
</article>
{% else %}
<p>이 분석 실행에 등록된 취재 아이디어가 없습니다.</p>
{% endfor %}
</body>
</html>
""")


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
    finally:
        connection.close()

    evidence = defaultdict(list)
    for item in evidence_rows:
        evidence[item["article_idea_id"]].append(item)

    return ideas, evidence


@app.get("/review", response_class=HTMLResponse)
def review_page(run_id: int = 1):
    if run_id <= 0:
        raise HTTPException(400, "Invalid analysis run ID")

    ideas, evidence = load_review_data(run_id)

    return PAGE.render(
        run_id=run_id,
        ideas=ideas,
        evidence=evidence,
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
        url=f"/review?run_id={run_id}",
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
from .pdf import extract_pdf, locate_pdf_excerpt_segments
from .source_repository import save_source_evidence
from .idea_repository import link_article_evidence


UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@app.get("/", response_class=HTMLResponse)
def upload_page():
    return """
    <!doctype html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <title>RGF - 정책자료 분석</title>
        <style>
            body {
                font-family: system-ui, sans-serif;
                max-width: 720px;
                margin: 50px auto;
                padding: 0 20px;
                line-height: 1.7;
            }
            label {
                display: block;
                margin: 20px 0;
            }
            input {
                display: block;
                width: 100%;
                padding: 10px;
                box-sizing: border-box;
            }
            button {
                padding: 12px 24px;
                cursor: pointer;
            }
            .notice {
                background: #f5f5f5;
                padding: 16px;
                border-radius: 6px;
            }
        </style>
    </head>
    <body>
        <h1>RGF — Reporting Gap Finder</h1>
        <p>
            정부 정책자료를 분석해 정보 공백과
            추가 취재가 필요한 지점을 찾아냅니다.
        </p>

        <form method="post"
              action="/analyze"
              enctype="multipart/form-data">

            <label>
                정책자료 제목
                <input type="text" name="title" required maxlength="500">
            </label>

            <label>
                발표 기관 (선택)
                <input type="text" name="organization" maxlength="255">
            </label>

            <label>
                PDF 파일
                <input type="file"
                       name="file"
                       accept=".pdf,application/pdf"
                       required>
            </label>

            <button type="submit">AI 분석 시작</button>
        </form>

        <p class="notice">
            텍스트 추출이 가능한 PDF만 지원합니다.
            최대 파일 크기는 10MB입니다.
            분석을 시작하면 OpenAI API 요금이 발생합니다.
            분석 완료 후 기자 검토 화면으로 이동합니다.
        </p>

        <p><a href="/review?run_id=1">기존 분석 결과 보기</a></p>
    </body>
    </html>
    """


@app.post("/analyze")
def analyze_pdf(
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

    # Check AI configuration before saving a new source document.
    client = OpenAIJSONClient()

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = UPLOAD_DIR / f"{uuid4().hex}.pdf"
    pdf_path.write_bytes(data)

    registered = False

    try:
        # Register the original PDF in MySQL.
        source_id = register_pdf(
            file_path=pdf_path,
            title=title,
            organization=organization or None,
        )
        registered = True

        # Run the existing three-stage AI pipeline.
        structured, analysis = Pipeline(client).run(pdf_path)

        # Save the analysis.
        run_id = save_analysis_run(
            source_document_id=source_id,
            structured=structured,
            analysis=analysis,
            model_name=client.model,
            prompt_version="v0.1",
        )

        # Save reporting leads and exact-match source excerpts.
        source_text = extract_pdf(pdf_path)

        for lead in analysis.reporting_leads:
            idea_id = save_article_idea(
                analysis=analysis,
                analysis_run_id=run_id,
                lead_id=lead.lead_id,
            )

            segments = locate_pdf_excerpt_segments(
                source_text,
                lead.provenance.excerpt,
            )

            for segment in segments:
                if len(segment["pages"]) != 1:
                    continue

                page_number = segment["pages"][0]

                evidence_id = save_source_evidence(
                    source_document_id=source_id,
                    page_number=page_number,
                    content=segment["excerpt"],
                )

                link_article_evidence(
                    article_idea_id=idea_id,
                    source_evidence_id=evidence_id,
                    relation_type="CONTEXT",
                    explanation=(
                        "Exact excerpt text matched the source PDF. "
                        "Relevance and supporting relationship "
                        "have not been verified."
                    ),
                )

    except Exception:
        # Only remove the file if it was never registered in MySQL.
        if not registered:
            pdf_path.unlink(missing_ok=True)
        raise

    return RedirectResponse(
        url=f"/review?run_id={run_id}",
        status_code=303,
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
