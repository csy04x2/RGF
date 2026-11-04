
import argparse
from pathlib import Path

from .analysis_repository import save_analysis_run
from .idea_repository import save_article_idea
from .llm import OpenAIJSONClient
from .pipeline import Pipeline
from .renderer import render
from .source_repository import get_source_document
from .status_review import find_status_warnings


def main():
    parser = argparse.ArgumentParser(
        description="RGF standalone v0.1"
    )

    parser.add_argument("--input", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--html-output", required=True)
    parser.add_argument("--model")
    parser.add_argument(
        "--source-id",
        type=int,
        help="Existing MySQL source document ID; enables DB saving",
    )

    args = parser.parse_args()

    # Verify the existing source before spending money on AI calls.
    if args.source_id is not None:
        if args.source_id <= 0:
            parser.error("--source-id must be positive")

        source_document = get_source_document(args.source_id)

        if source_document is None:
            parser.error("Source document not found in MySQL")

        saved_path = source_document["file_path"]

        if (
            source_document["source_type"] != "PDF"
            or not saved_path
            or Path(saved_path).resolve() != Path(args.input).resolve()
        ):
            parser.error(
                "Source document does not match the input PDF"
            )

    # Run AI analysis and structural validation.
    client = OpenAIJSONClient(args.model)
    structured, result = Pipeline(client).run(args.input)

    warnings = find_status_warnings(result)
    html = render(result, warnings=warnings)

    Path(args.json_output).write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    Path(args.html_output).write_text(
        html,
        encoding="utf-8",
    )

    print("VALIDATION: PASS")
    print(f"POLICY STATUS REVIEW: {len(warnings)} warning(s)")

    for warning in warnings:
        print(f"- {warning}")

    # Database saving is optional.
    if args.source_id is not None:
        run_id = save_analysis_run(
            source_document_id=args.source_id,
            structured=structured,
            analysis=result,
            model_name=client.model,
            prompt_version="v0.1",
        )

        saved_count = 0

        for lead in result.reporting_leads:
            save_article_idea(
                analysis=result,
                analysis_run_id=run_id,
                lead_id=lead.lead_id,
            )
            saved_count += 1

        print(f"DATABASE ANALYSIS RUN ID: {run_id}")
        print(f"DATABASE ARTICLE IDEAS SAVED: {saved_count}")


if __name__ == "__main__":
    main()
