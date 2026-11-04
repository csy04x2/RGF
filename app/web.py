
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
