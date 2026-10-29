
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
