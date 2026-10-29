from datetime import timezone
from app.review import JournalistReview
import json

from app.database import get_connection
from app.models import ReportingAnalysis


PRIORITY_MAP = {
    "A": "HIGH",
    "B": "MEDIUM",
    "C": "LOW",
}


def save_article_idea(
    analysis: ReportingAnalysis,
    analysis_run_id: int,
    lead_id: str,
) -> int:
    """Save one reporting lead to MySQL."""

    lead = next(
        (
            item for item in analysis.reporting_leads
            if item.lead_id == lead_id
        ),
        None,
    )

    if lead is None:
        raise ValueError(
            f"존재하지 않는 취재 아이디어입니다: {lead_id}"
        )

    priority = PRIORITY_MAP[lead.priority]

    sql = """
        INSERT INTO article_ideas (
            analysis_run_id,
            lead_id,
            title,
            angle,
            why_it_matters,
            reporting_questions,
            evidence_needed,
            reporting_targets,
            priority
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        analysis_run_id,
        lead.lead_id,
        lead.reporting_question[:500],
        lead.material_implication,
        lead.why_it_matters,
        json.dumps(
            [lead.reporting_question],
            ensure_ascii=False,
        ),
        json.dumps(
            lead.evidence_needed,
            ensure_ascii=False,
        ),
        json.dumps(
            lead.targets,
            ensure_ascii=False,
        ),
        priority,
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            saved_id = cursor.lastrowid

        connection.commit()
        return saved_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_journalist_review(
    analysis_run_id: int,
    review: JournalistReview,
) -> None:
    """Save a journalist's review of an existing article idea."""

    if analysis_run_id <= 0:
        raise ValueError("유효한 분석 실행 ID가 필요합니다.")

    if review.status == "보류" and not review.review_note.strip():
        raise ValueError("보류할 때는 검토 사유를 입력해야 합니다.")

    if review.status != "검토대기" and review.reviewed_at is None:
        raise ValueError("승인·보류에는 검토 시각이 필요합니다.")

    reviewed_at = (
        review.reviewed_at.astimezone(timezone.utc).replace(tzinfo=None)
        if review.reviewed_at is not None
        else None
    )

    sql = """
        UPDATE article_ideas
        SET review_status = %s,
            review_note = %s,
            reviewer = %s,
            reviewed_at = %s
        WHERE analysis_run_id = %s
          AND lead_id = %s
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    review.status,
                    review.review_note,
                    review.reviewer,
                    reviewed_at,
                    analysis_run_id,
                    review.lead_id,
                ),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    SELECT id
                    FROM article_ideas
                    WHERE analysis_run_id = %s
                      AND lead_id = %s
                    FOR UPDATE
                    """,
                    (analysis_run_id, review.lead_id),
                )

                if cursor.fetchone() is None:
                    raise ValueError(
                        "검토 대상이 존재하지 않습니다: "
                        f"{review.lead_id}"
                    )

            elif cursor.rowcount != 1:
                raise ValueError(
                    "예상하지 못한 검토 대상 수입니다: "
                    f"{cursor.rowcount}"
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
