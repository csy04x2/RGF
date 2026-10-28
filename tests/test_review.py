
import pytest
from pydantic import ValidationError

from app.review import JournalistReview, update_review


def make_review():
    return JournalistReview(
        lead_id="RL7",
        reviewer="테스트 기자",
    )


def test_default_review_status():
    review = make_review()

    assert review.status == "검토대기"
    assert review.reviewed_at is None


def test_approve_review():
    review = make_review()

    updated = update_review(
        review,
        status="승인",
        review_note="취재 가치와 원문 근거 확인",
    )

    assert updated.status == "승인"
    assert updated.review_note == "취재 가치와 원문 근거 확인"
    assert updated.reviewed_at is not None


def test_hold_review():
    review = make_review()

    updated = update_review(
        review,
        status="보류",
        review_note="정책 근거 연결 재검토 필요",
    )

    assert updated.status == "보류"
    assert updated.review_note == "정책 근거 연결 재검토 필요"


def test_hold_requires_reason():
    review = make_review()

    with pytest.raises(ValueError, match="보류할 때는"):
        update_review(
            review,
            status="보류",
            review_note="   ",
        )


def test_invalid_status_rejected():
    review = make_review()

    with pytest.raises(ValidationError):
        update_review(
            review,
            status="자동승인",
        )


def test_original_review_is_preserved():
    review = make_review()

    updated = update_review(
        review,
        status="승인",
    )

    assert review.status == "검토대기"
    assert review.reviewed_at is None
    assert updated.status == "승인"


from app.review import save_review, load_review


def test_save_and_load_review(tmp_path):
    # 1. 기자 검토 기록 생성
    review = JournalistReview(
        lead_id="RL7",
        reviewer="테스트 기자",
    )

    updated = update_review(
        review,
        status="보류",
        review_note="예방교육 취재 아이디어의 정책 근거 연결 재검토 필요",
    )

    # 2. 임시 JSON 파일에 저장
    file_path = tmp_path / "reviews" / "RL7.json"

    save_review(
    updated,
    file_path,
    make_analysis_for_review(),
)

    assert file_path.exists()

    # 3. 파일을 다시 읽기
    loaded = load_review(file_path)

    # 4. 저장 전후 데이터 비교
    assert loaded == updated
    assert loaded.lead_id == "RL7"
    assert loaded.status == "보류"
    assert loaded.reviewer == "테스트 기자"
    assert loaded.review_note == (
        "예방교육 취재 아이디어의 정책 근거 연결 재검토 필요"
    )
    assert loaded.reviewed_at is not None


def test_load_invalid_review_rejected(tmp_path):
    # 잘못된 상태값을 가진 JSON 파일
    file_path = tmp_path / "invalid.json"

    file_path.write_text(
        '{"lead_id":"RL7","reviewer":"테스트 기자",'
        '"status":"자동승인"}',
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_review(file_path)

from app.models import ReportingAnalysis
from app.review import validate_review_target


def make_analysis_for_review():
    return ReportingAnalysis.model_validate({
        "discovery_summary": "테스트 분석",
        "policy_actions": [],
        "material_changes": [],
        "reporting_leads": [
            {
                "lead_id": "RL7",
                "priority": "C",
                "lenses": ["OUTCOME"],
                "related_items": [],
                "source_signal": "예방교육 확대 계획",
                "material_implication": "교육 효과 검증 필요",
                "unknown": "실제 시행 여부",
                "reporting_question": "예방교육이 실제 시행됐는가?",
                "why_it_matters": "정책 실효성 검증",
                "evidence_needed": [],
                "targets": [],
                "provenance": {
                    "page": 1,
                    "excerpt": "예방교육 확대",
                },
            }
        ],
        "follow_ups": [],
        "perspectives": [],
        "reporting_actions": [],
        "limitations": [],
    })


def test_valid_review_target():
    analysis = make_analysis_for_review()

    review = JournalistReview(
        lead_id="RL7",
        reviewer="테스트 기자",
    )

    validate_review_target(analysis, review)


def test_nonexistent_review_target_rejected():
    analysis = make_analysis_for_review()

    review = JournalistReview(
        lead_id="RL999",
        reviewer="테스트 기자",
    )

    with pytest.raises(ValueError, match="존재하지 않는 취재 아이디어"):
        validate_review_target(analysis, review)


def test_policy_action_cannot_be_reviewed_as_lead():
    analysis = make_analysis_for_review()

    review = JournalistReview(
        lead_id="PA1",
        reviewer="테스트 기자",
    )

    with pytest.raises(ValueError, match="존재하지 않는 취재 아이디어"):
        validate_review_target(analysis, review)


def test_invalid_review_does_not_create_file(tmp_path):
    analysis = make_analysis_for_review()

    review = JournalistReview(
        lead_id="RL999",
        reviewer="테스트 기자",
    )

    file_path = tmp_path / "reviews" / "RL999.json"

    with pytest.raises(ValueError, match="존재하지 않는 취재 아이디어"):
        save_review(review, file_path, analysis)

    # 잘못된 검토 기록은 저장되지 않아야 한다.
    assert not file_path.exists()


def test_invalid_review_does_not_overwrite_existing_file(tmp_path):
    analysis = make_analysis_for_review()

    file_path = tmp_path / "reviews" / "review.json"

    # 먼저 정상 검토 결과를 저장한다.
    valid_review = JournalistReview(
        lead_id="RL7",
        reviewer="테스트 기자",
    )

    save_review(valid_review, file_path, analysis)

    original_content = file_path.read_text(encoding="utf-8")

    # 존재하지 않는 아이디어로 기존 파일 덮어쓰기 시도
    invalid_review = JournalistReview(
        lead_id="RL999",
        reviewer="테스트 기자",
    )

    with pytest.raises(ValueError, match="존재하지 않는 취재 아이디어"):
        save_review(invalid_review, file_path, analysis)

    # 기존 파일 내용이 그대로 보존되어야 한다.
    assert file_path.read_text(encoding="utf-8") == original_content
