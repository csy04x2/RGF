
import argparse
from pathlib import Path

from .llm import OpenAIJSONClient
from .pipeline import Pipeline
from .renderer import render
from .status_review import find_status_warnings


def main():
    parser = argparse.ArgumentParser(
        description="RGF standalone v0.1"
    )

    parser.add_argument("--input", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--html-output", required=True)
    parser.add_argument("--model")

    args = parser.parse_args()

    # 1. Run AI analysis and structural validation.
    _, result = Pipeline(
        OpenAIJSONClient(args.model)
    ).run(args.input)

    # 2. Check policy implementation statuses.
    warnings = find_status_warnings(result)

    # 3. Save the original analysis results.
    html = render(result, warnings=warnings)

    Path(args.json_output).write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    Path(args.html_output).write_text(
        html,
        encoding="utf-8",
    )

    # 4. Display validation and review results.
    print("VALIDATION: PASS")
    print(f"POLICY STATUS REVIEW: {len(warnings)} warning(s)")

    for warning in warnings:
        print(f"- {warning}")


if __name__ == "__main__":
    main()
