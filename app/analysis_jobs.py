"""Database-backed state for a long-running PDF analysis task.

FastAPI BackgroundTasks executes after the short HTTP response. The Postgres
record persists status across page reloads. A Railway process restart can still
interrupt work; this is not a durable worker queue.
"""
import logging
from pathlib import Path

from .database import get_connection, is_postgres
from .idea_repository import save_article_idea, link_article_evidence
from .llm import OpenAIJSONClient
from .pdf import extract_pdf, locate_pdf_excerpt_segments
from .pipeline import Pipeline
from .source_repository import save_source_evidence

logger = logging.getLogger(__name__)


def _execute(sql, values):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_pending_run(source_id: int, model_name: str) -> int:
    connection = get_connection()
    try:
        postgres = is_postgres(connection)
        sql = '''INSERT INTO analysis_runs
            (source_document_id, model_name, prompt_version, status, started_at)
            VALUES (%s, %s, 'v0.1', 'PENDING', NULL)'''
        if postgres:
            sql += " RETURNING id"
        with connection.cursor() as cursor:
            cursor.execute(sql, (source_id, model_name))
            run_id = cursor.fetchone()["id"] if postgres else cursor.lastrowid
        connection.commit()
        return run_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _set_running(run_id: int):
    _execute(
        "UPDATE analysis_runs SET status = 'RUNNING', started_at = CURRENT_TIMESTAMP "
        "WHERE id = %s AND status = 'PENDING'",
        (run_id,),
    )


def _set_completed(run_id: int, structured, analysis):
    connection = get_connection()
    try:
        postgres = is_postgres(connection)
        sql = '''UPDATE analysis_runs
            SET status = 'COMPLETED', structured_source_json = %s,
                analysis_json = %s, completed_at = CURRENT_TIMESTAMP,
                error_message = NULL
            WHERE id = %s'''
        if postgres:
            sql = sql.replace('structured_source_json = %s', 'structured_source_json = %s::jsonb')
            sql = sql.replace('analysis_json = %s', 'analysis_json = %s::jsonb')
        with connection.cursor() as cursor:
            cursor.execute(sql, (structured.model_dump_json(), analysis.model_dump_json(), run_id))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _set_failed(run_id: int):
    _execute(
        "UPDATE analysis_runs SET status = 'FAILED', error_message = %s "
        "WHERE id = %s",
        ("Analysis failed. See Railway application logs.", run_id),
    )


def run_analysis_job(run_id: int, source_id: int, pdf_path: str):
    """Run the existing three-stage pipeline; save verified evidence only."""
    try:
        _set_running(run_id)
        client = OpenAIJSONClient()
        structured, analysis = Pipeline(client).run(Path(pdf_path))
        source_text = extract_pdf(pdf_path)

        # Do not mark the run completed until all reporting leads are saved.
        for lead in analysis.reporting_leads:
            idea_id = save_article_idea(
                analysis=analysis, analysis_run_id=run_id, lead_id=lead.lead_id
            )
            try:
                preferred_page = int(lead.provenance.page)
            except (TypeError, ValueError):
                preferred_page = None
            segments = locate_pdf_excerpt_segments(
                source_text, lead.provenance.excerpt, preferred_page=preferred_page
            )
            for segment in segments:
                if len(segment['pages']) != 1:
                    continue
                evidence_id = save_source_evidence(
                    source_document_id=source_id,
                    page_number=segment['pages'][0],
                    content=segment['excerpt'],
                )
                link_article_evidence(
                    article_idea_id=idea_id,
                    source_evidence_id=evidence_id,
                    relation_type='CONTEXT',
                    explanation=(
                        'Exact excerpt matched the source PDF. '
                        'Relevance to this reporting lead has not been independently verified.'
                    ),
                )
        _set_completed(run_id, structured, analysis)
        logger.info('RGF analysis #%s completed', run_id)
    except Exception:
        logger.exception('RGF analysis #%s failed', run_id)
        try:
            _set_failed(run_id)
        except Exception:
            logger.exception('Could not persist FAILED status for analysis #%s', run_id)
