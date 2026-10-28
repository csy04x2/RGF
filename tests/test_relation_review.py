
import pytest
from pydantic import ValidationError

from app.relation_review import RelationReview, RelationReviewResult


def test_valid_relation_review():
    review = RelationReview(
        lead_id="RL7",
        target_type="policy_action",
        target_id="PA1",
        verdict="UNRELATED",
        reason="예방교육 취재 질문과 형사처벌 정책의 직접적 관련성이 부족함",
        suggested_action="예방교육 정책을 연결하거나 연결 근거를 재검토",
    )

    assert review.verdict == "UNRELATED"
    assert review.target_id == "PA1"


def test_invalid_verdict_rejected():
    with pytest.raises(ValidationError):
        RelationReview(
            lead_id="RL7",
            target_type="policy_action",
            target_id="PA1",
            verdict="WRONG",
            reason="관련성 부족",
            suggested_action="연결 수정",
        )


def test_empty_reason_rejected():
    with pytest.raises(ValidationError):
        RelationReview(
            lead_id="RL7",
            target_type="policy_action",
            target_id="PA1",
            verdict="QUESTIONABLE",
            reason="",
            suggested_action="기자 검토",
        )


def test_relation_review_result():
    result = RelationReviewResult(
        reviews=[
            RelationReview(
                lead_id="RL7",
                target_type="policy_action",
                target_id="PA1",
                verdict="UNRELATED",
                reason="취재 질문과 정책 조치의 주제가 다름",
                suggested_action="관련 정책 근거로 연결 수정",
            )
        ]
    )

    assert len(result.reviews) == 1
    assert result.reviews[0].lead_id == "RL7"


from app.models import ReportingAnalysis
from app.relation_review import review_relations


def make_review_analysis():
    return ReportingAnalysis.model_validate({
        "discovery_summary": "Test",
        "policy_actions": [
            {
                "id": "PA1",
                "action": "형사처벌 강화",
                "status": "IN_EFFECT",
                "responsible_actors": [],
                "affected_groups": [],
                "dependencies": [],
                "provenance": {
                    "page": 1,
                    "excerpt": "형사처벌 강화"
                },
            }
        ],
        "material_changes": [],
        "reporting_leads": [
            {
                "lead_id": "RL1",
                "priority": "A",
                "lenses": ["IMPLEMENTATION"],
                "related_items": [
                    {
                        "type": "policy_action",
                        "id": "PA1",
                        "description": "형사처벌 강화",
                    }
                ],
                "source_signal": "법 개정",
                "material_implication": "제도 변화",
                "unknown": "집행 실태",
                "reporting_question": "처벌 규정이 실제로 집행되는가?",
                "why_it_matters": "정책 실효성 검증",
                "evidence_needed": [],
                "targets": [],
                "provenance": {
                    "page": 1,
                    "excerpt": "법 개정"
                },
            }
        ],
        "follow_ups": [],
        "perspectives": [],
        "reporting_actions": [],
        "limitations": [],
    })


class FakeRelationClient:
    def __init__(self, reviews):
        self.reviews = reviews

    def parse(self, prompt, schema):
        return schema.model_validate({"reviews": self.reviews})


def test_relation_review_preserves_links():
    analysis = make_review_analysis()

    client = FakeRelationClient([
        {
            "lead_id": "RL1",
            "target_type": "policy_action",
            "target_id": "PA1",
            "verdict": "SUPPORTED",
            "reason": "처벌 규정의 집행 여부를 직접 검증하는 관계",
            "suggested_action": "연결 유지",
        }
    ])

    result = review_relations(analysis, client)

    assert len(result.reviews) == 1
    assert result.reviews[0].target_id == "PA1"


def test_relation_review_rejects_missing_links():
    analysis = make_review_analysis()
    client = FakeRelationClient([])

    with pytest.raises(ValueError, match="preserve relationship IDs"):
        review_relations(analysis, client)


def test_relation_review_rejects_changed_ids():
    analysis = make_review_analysis()

    client = FakeRelationClient([
        {
            "lead_id": "RL1",
            "target_type": "policy_action",
            "target_id": "PA99",
            "verdict": "SUPPORTED",
            "reason": "테스트",
            "suggested_action": "확인",
        }
    ])

    with pytest.raises(ValueError, match="preserve relationship IDs"):
        review_relations(analysis, client)


from app.relation_review_prompt import (
    RELATION_REVIEW_INSTRUCTIONS,
    build_relation_review_prompt,
)


def test_relation_review_prompt_distinguishes_relevance_from_proof():
    prompt = RELATION_REVIEW_INSTRUCTIONS

    assert "RELEVANCE VS. PROOF" in prompt
    assert "Do not assign QUESTIONABLE solely" in prompt
    assert "Assign SUPPORTED when the linked policy directly" in prompt
    assert "Assign UNRELATED when the linked policy concerns" in prompt


def test_relation_review_prompt_preserves_review_ids():
    prompt = RELATION_REVIEW_INSTRUCTIONS

    assert "Preserve the original lead_id" in prompt
    assert "Return one review for every supplied relationship" in prompt


def test_relation_review_prompt_contains_relationship_data():
    items = [
        {
            "lead_id": "RL7",
            "reporting_question": "학교 예방교육이 실제 시행됐는가?",
            "target_type": "policy_action",
            "target_id": "PA1",
            "target_description": "형사처벌 강화",
        }
    ]

    prompt = build_relation_review_prompt(items)

    assert "RL7" in prompt
    assert "PA1" in prompt
    assert "학교 예방교육이 실제 시행됐는가?" in prompt
    assert "형사처벌 강화" in prompt


from app.renderer import render


def test_integrated_html_preserves_reviews_and_objects():
    analysis = make_review_analysis()

    reviews = RelationReviewResult.model_validate({
        "reviews": [
            {
                "lead_id": "RL1",
                "target_type": "policy_action",
                "target_id": "PA1",
                "verdict": "UNRELATED",
                "reason": "취재 질문과 연결된 정책의 내용이 다름",
                "suggested_action": "정책 근거를 다시 확인하세요",
            }
        ]
    })

    html = render(
        analysis,
        warnings=["PA1: 정책 시행 상태 확인 필요"],
        relation_reviews=reviews,
    )

    # 정책 시행 상태 경고가 표시되어야 한다.
    assert "정책 시행 상태 검토 필요" in html
    assert "PA1: 정책 시행 상태 확인 필요" in html

    # AI 관계 검토 결과가 표시되어야 한다.
    assert "AI 관계 검토 결과" in html
    assert "UNRELATED" in html
    assert "취재 질문과 연결된 정책의 내용이 다름" in html
    assert "정책 근거를 다시 확인하세요" in html

    # 기존 분석 객체가 삭제되면 안 된다.
    assert 'data-object-id="PA1"' in html
    assert 'data-object-id="RL1"' in html


def test_integrated_html_without_reviews():
    analysis = make_review_analysis()

    html = render(analysis)

    # 관계 검토 결과를 입력하지 않아도 기존 보고서는 생성돼야 한다.
    assert "RGF Reporting Brief" in html
    assert 'data-object-id="PA1"' in html
    assert 'data-object-id="RL1"' in html
    assert "AI 관계 검토 결과" not in html
