
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ReviewStatus = Literal["검토대기", "승인", "보류"]


class JournalistReview(BaseModel):
    """A journalist's review of one reporting lead."""

    lead_id: str = Field(min_length=1)
    status: ReviewStatus = "검토대기"
    reviewer: str = Field(min_length=1)
    review_note: str = ""
    reviewed_at: datetime | None = None


def update_review(
    review: JournalistReview,
    status: ReviewStatus,
    review_note: str = "",
) -> JournalistReview:
    """Update a journalist's decision without modifying the original."""

    from datetime import timezone

    if status == "보류" and not review_note.strip():
        raise ValueError("보류할 때는 검토 사유를 입력해야 합니다.")

    return JournalistReview(
        lead_id=review.lead_id,
        status=status,
        reviewer=review.reviewer,
        review_note=review_note,
        reviewed_at=(
            datetime.now(timezone.utc)
            if status != "검토대기"
            else None
        ),
    )

from pathlib import Path



def save_review(
    review: JournalistReview,
    file_path: str | Path,
    analysis: ReportingAnalysis,
) -> None:
    """Save a review only if its reporting lead exists."""

    # Validate before creating or writing any file.
    validate_review_target(analysis, review)

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        review.model_dump_json(indent=2),
        encoding="utf-8",
    )



def load_review(
    file_path: str | Path,
) -> JournalistReview:
    """Load and validate a saved journalist review."""

    path = Path(file_path)

    return JournalistReview.model_validate_json(
        path.read_text(encoding="utf-8")
    )

from app.models import ReportingAnalysis


def validate_review_target(
    analysis: ReportingAnalysis,
    review: JournalistReview,
) -> None:
    """Check that the reviewed lead exists in the analysis."""

    lead_ids = {
        lead.lead_id
        for lead in analysis.reporting_leads
    }

    if review.lead_id not in lead_ids:
        raise ValueError(
            f"존재하지 않는 취재 아이디어입니다: {review.lead_id}"
        )
