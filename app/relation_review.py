
from typing import Literal

from pydantic import BaseModel, Field


class RelationReview(BaseModel):
    lead_id: str
    target_type: Literal["policy_action", "material_change"]
    target_id: str

    verdict: Literal[
        "SUPPORTED",
        "QUESTIONABLE",
        "UNRELATED",
    ]

    reason: str = Field(min_length=1)
    suggested_action: str = Field(min_length=1)


class RelationReviewResult(BaseModel):
    reviews: list[RelationReview]


from app.models import ReportingAnalysis


def build_relation_review_items(
    analysis: ReportingAnalysis,
) -> list[dict]:
    """Build evidence packages for reviewing lead-to-policy links."""

    policies = {
        item.id: item
        for item in analysis.policy_actions
    }

    changes = {
        item.id: item
        for item in analysis.material_changes
    }

    items = []

    for lead in analysis.reporting_leads:
        for relation in lead.related_items:
            if relation.type == "policy_action":
                target = policies.get(relation.id)
                target_description = (
                    target.action if target else None
                )

            elif relation.type == "material_change":
                target = changes.get(relation.id)
                target_description = (
                    target.change if target else None
                )

            else:
                # source_claim is outside the current review scope.
                continue

            if target is None:
                continue

            items.append(
                {
                    "lead_id": lead.lead_id,
                    "reporting_question": lead.reporting_question,
                    "source_signal": lead.source_signal,
                    "lead_excerpt": lead.provenance.excerpt,
                    "target_type": relation.type,
                    "target_id": relation.id,
                    "target_description": target_description,
                    "target_excerpt": target.provenance.excerpt,
                }
            )

    return items


from app.relation_review_prompt import build_relation_review_prompt


def review_relations(analysis: ReportingAnalysis, client) -> RelationReviewResult:
    """Review semantic links without modifying the analysis."""

    items = build_relation_review_items(analysis)

    if not items:
        return RelationReviewResult(reviews=[])

    prompt = build_relation_review_prompt(items)

    result = client.parse(
        prompt,
        RelationReviewResult,
    )

    # Verify that the AI reviewed exactly the requested relationships.
    expected = [
        (item["lead_id"], item["target_type"], item["target_id"])
        for item in items
    ]

    actual = [
        (review.lead_id, review.target_type, review.target_id)
        for review in result.reviews
    ]

    if len(actual) != len(expected) or sorted(actual) != sorted(expected):
        raise ValueError(
            "AI relation review did not preserve relationship IDs and counts."
        )

    return result
