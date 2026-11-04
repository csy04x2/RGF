
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app import web
from app.models import ReportingAnalysis, SourceStructure
from tests.test_core import analysis_data, source_data


def test_web_pdf_analysis_flow(monkeypatch, tmp_path):
    structured = SourceStructure.model_validate(source_data())
    analysis = ReportingAnalysis.model_validate(analysis_data())

    client = MagicMock()
    client.model = "test-model"

    pipeline = MagicMock()
    pipeline.run.return_value = (structured, analysis)

    register = MagicMock(return_value=3)
    save_run = MagicMock(return_value=10)
    save_idea = MagicMock(return_value=20)
    save_evidence = MagicMock(return_value=30)
    link_evidence = MagicMock()

    monkeypatch.setattr(web, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(web, "OpenAIJSONClient", lambda: client)
    monkeypatch.setattr(web, "Pipeline", lambda _: pipeline)
    monkeypatch.setattr(web, "register_pdf", register)
    monkeypatch.setattr(web, "save_analysis_run", save_run)
    monkeypatch.setattr(web, "save_article_idea", save_idea)

    monkeypatch.setattr(
        web,
        "extract_pdf",
        lambda path: "[SOURCE PAGE 1]\ne",
    )
    monkeypatch.setattr(
        web,
        "save_source_evidence",
        save_evidence,
    )
    monkeypatch.setattr(
        web,
        "link_article_evidence",
        link_evidence,
    )

    test_client = TestClient(web.app)

    response = test_client.post(
        "/analyze",
        data={
            "title": "Test policy document",
            "organization": "Test ministry",
        },
        files={
            "file": (
                "test.pdf",
                b"%PDF-1.4\n%test",
                "application/pdf",
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/workspace/10"

    register.assert_called_once()
    assert register.call_args.kwargs["title"] == "Test policy document"

    pipeline.run.assert_called_once()

    save_run.assert_called_once_with(
        source_document_id=3,
        structured=structured,
        analysis=analysis,
        model_name="test-model",
        prompt_version="v0.1",
    )

    assert save_idea.call_count == len(analysis.reporting_leads)

    saved_ids = [
        call.kwargs["lead_id"]
        for call in save_idea.call_args_list
    ]

    assert saved_ids == [
        lead.lead_id
        for lead in analysis.reporting_leads
    ]

    save_evidence.assert_called_once_with(
        source_document_id=3,
        page_number=1,
        content="e",
    )

    link_evidence.assert_called_once_with(
        article_idea_id=20,
        source_evidence_id=30,
        relation_type="CONTEXT",
        explanation=(
            "Exact excerpt text matched the source PDF. "
            "Relevance and supporting relationship "
            "have not been verified."
        ),
    )
