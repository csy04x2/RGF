
import sys
from unittest.mock import MagicMock

from app import cli
from app.models import ReportingAnalysis, SourceStructure
from tests.test_core import analysis_data, source_data


def test_cli_saves_analysis_and_ideas(monkeypatch, tmp_path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    output_json = tmp_path / "result.json"
    output_html = tmp_path / "result.html"

    structured = SourceStructure.model_validate(source_data())
    analysis = ReportingAnalysis.model_validate(analysis_data())

    client = MagicMock()
    client.model = "test-model"

    pipeline = MagicMock()
    pipeline.run.return_value = (structured, analysis)

    save_run = MagicMock(return_value=10)
    save_idea = MagicMock(return_value=20)

    monkeypatch.setattr(cli, "OpenAIJSONClient", lambda model: client)
    monkeypatch.setattr(cli, "Pipeline", lambda client: pipeline)
    monkeypatch.setattr(cli, "save_analysis_run", save_run)
    monkeypatch.setattr(cli, "save_article_idea", save_idea)

    monkeypatch.setattr(
        cli,
        "get_source_document",
        lambda source_id: {
            "source_type": "PDF",
            "file_path": str(pdf),
        },
    )

    monkeypatch.setattr(
        cli,
        "render",
        lambda analysis, warnings: "<html></html>",
    )

    monkeypatch.setattr(
        cli,
        "find_status_warnings",
        lambda analysis: [],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.cli",
            "--input", str(pdf),
            "--json-output", str(output_json),
            "--html-output", str(output_html),
            "--source-id", "3",
        ],
    )

    cli.main()

    assert output_json.exists()
    assert output_html.exists()

    save_run.assert_called_once_with(
        source_document_id=3,
        structured=structured,
        analysis=analysis,
        model_name="test-model",
        prompt_version="v0.1",
    )

    assert save_idea.call_count == len(analysis.reporting_leads)

    saved_lead_ids = [
        call.kwargs["lead_id"]
        for call in save_idea.call_args_list
    ]

    assert saved_lead_ids == [
        lead.lead_id
        for lead in analysis.reporting_leads
    ]


def test_cli_without_source_id_skips_database(monkeypatch, tmp_path):
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    structured = SourceStructure.model_validate(source_data())
    analysis = ReportingAnalysis.model_validate(analysis_data())

    client = MagicMock()
    client.model = "test-model"

    pipeline = MagicMock()
    pipeline.run.return_value = (structured, analysis)

    save_run = MagicMock()
    save_idea = MagicMock()

    monkeypatch.setattr(cli, "OpenAIJSONClient", lambda model: client)
    monkeypatch.setattr(cli, "Pipeline", lambda client: pipeline)
    monkeypatch.setattr(cli, "save_analysis_run", save_run)
    monkeypatch.setattr(cli, "save_article_idea", save_idea)

    monkeypatch.setattr(
        cli,
        "render",
        lambda analysis, warnings: "<html></html>",
    )

    monkeypatch.setattr(
        cli,
        "find_status_warnings",
        lambda analysis: [],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.cli",
            "--input", str(pdf),
            "--json-output", str(tmp_path / "result.json"),
            "--html-output", str(tmp_path / "result.html"),
        ],
    )

    cli.main()

    save_run.assert_not_called()
    save_idea.assert_not_called()
