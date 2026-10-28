
from app.models import ReportingAnalysis


def find_status_warnings(analysis: ReportingAnalysis) -> list[str]:
    """Find possible policy implementation status conflicts."""

    warnings = []

    for change in analysis.material_changes:
        if "implementation_status" not in change.model_fields_set:
            warnings.append(
                f"{change.id}: 정책 시행 상태가 분석 결과에 "
                "포함되지 않았습니다. 기자 확인이 필요합니다."
            )

    proposal_phrases = (
        "개정 추진",
        "의무화 추진",
        "도입 추진",
        "설치 추진",
        "시행 예정",
        "법 개정 필요",
    )

    items = [
        (
            action.id,
            action.status,
            action.provenance.excerpt or "",
        )
        for action in analysis.policy_actions
    ]

    items += [
        (
            change.id,
            change.implementation_status,
            change.provenance.excerpt or "",
        )
        for change in analysis.material_changes
    ]

    for item_id, status, excerpt in items:
        if status != "IN_EFFECT":
            continue

        if any(phrase in excerpt for phrase in proposal_phrases):
            warnings.append(
                f"{item_id}: 시행 중(IN_EFFECT)으로 분류됐지만 "
                "원문에 추진·예정 표현이 있습니다. "
                "정책 시행 여부를 확인하세요."
            )

    return warnings
