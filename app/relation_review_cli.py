
import argparse
import json
from pathlib import Path

from .llm import OpenAIJSONClient
from .models import ReportingAnalysis
from .relation_review import review_relations


def main():
    parser = argparse.ArgumentParser(
        description="RGF semantic relation review"
    )

    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.resolve() == output_path.resolve():
        parser.error("입력 파일과 출력 파일은 달라야 합니다.")

    # Load the existing analysis. Do not regenerate it.
    data = json.loads(
        input_path.read_text(encoding="utf-8")
    )
    analysis = ReportingAnalysis.model_validate(data)

    # Review relationships without editing the analysis.
    client = OpenAIJSONClient(args.model)
    result = review_relations(analysis, client)

    # Save review results in a separate file.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print(f"RELATION REVIEW: {len(result.reviews)} reviewed")

    for review in result.reviews:
        if review.verdict != "SUPPORTED":
            print(
                f"- {review.lead_id} -> {review.target_id}: "
                f"{review.verdict} | {review.reason}"
            )


if __name__ == "__main__":
    main()
