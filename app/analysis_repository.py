
from app.database import get_connection
from app.models import ReportingAnalysis, SourceStructure
from app.validation import validate_integrity


def save_analysis_run(
    source_document_id: int,
    structured: SourceStructure | None,
    analysis: ReportingAnalysis,
    model_name: str,
    prompt_version: str,
) -> int:
    """Save a completed AI analysis run to MySQL."""

    if source_document_id <= 0:
        raise ValueError("유효한 정책자료 ID가 필요합니다.")

    if not model_name.strip():
        raise ValueError("AI 모델 이름이 필요합니다.")

    if not prompt_version.strip():
        raise ValueError("프롬프트 버전이 필요합니다.")

    # Reject structurally invalid analyses before saving.
    validate_integrity(analysis)

    sql = """
        INSERT INTO analysis_runs (
            source_document_id,
            model_name,
            prompt_version,
            status,
            structured_source_json,
            analysis_json,
            started_at,
            completed_at
        )
        VALUES (%s, %s, %s, 'COMPLETED', %s, %s, NULL, UTC_TIMESTAMP())
    """

    values = (
        source_document_id,
        model_name.strip(),
        prompt_version.strip(),
        structured.model_dump_json() if structured is not None else None,
        analysis.model_dump_json(),
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            run_id = cursor.lastrowid

        connection.commit()
        return run_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
