
from app.models import ReportingAnalysis
from app.status_review import find_status_warnings


def test_proposed_policy_marked_in_effect():
    data = {
        "discovery_summary": "테스트",
        "policy_actions": [
            {
                "id": "PA1",
                "action": "삭제 의무화",
                "status": "IN_EFFECT",
                "responsible_actors": ["정부"],
                "affected_groups": ["플랫폼"],
                "dependencies": [],
                "provenance": {
                    "page": 1,
                    "excerpt": "삭제 의무화 추진"
                }
            }
        ],
        "material_changes": [],
        "reporting_leads": [],
        "follow_ups": [],
        "perspectives": [],
        "reporting_actions": [],
        "limitations": []
    }

    analysis = ReportingAnalysis.model_validate(data)
    warnings = find_status_warnings(analysis)

    assert len(warnings) == 1
    assert "PA1" in warnings[0]


def test_proposed_policy_not_marked_in_effect():
    data = {
        "discovery_summary": "테스트",
        "policy_actions": [
            {
                "id": "PA1",
                "action": "삭제 의무화",
                "status": "LEGISLATION_REQUIRED",
                "responsible_actors": ["정부"],
                "affected_groups": ["플랫폼"],
                "dependencies": [],
                "provenance": {
                    "page": 1,
                    "excerpt": "삭제 의무화 추진"
                }
            }
        ],
        "material_changes": [],
        "reporting_leads": [],
        "follow_ups": [],
        "perspectives": [],
        "reporting_actions": [],
        "limitations": []
    }

    analysis = ReportingAnalysis.model_validate(data)
    warnings = find_status_warnings(analysis)

    assert warnings == []


def test_status_warnings_appear_in_html():
    from app.renderer import render

    data = {
        "discovery_summary": "Test analysis",
        "policy_actions": [],
        "material_changes": [
            {
                "id": "MC1",
                "change": "Test change",
                "before": "Before",
                "after": "After",
                "affected_groups": [],
                "analytical_implication": "Impact",
                "unknown": "Unknown",
                "provenance": {"page": 1, "excerpt": "Test excerpt"},
            }
        ],
        "reporting_leads": [],
        "follow_ups": [],
        "perspectives": [],
        "reporting_actions": [],
        "limitations": [],
    }

    analysis = ReportingAnalysis.model_validate(data)
    warnings = find_status_warnings(analysis)
    html = render(analysis, warnings=warnings)

    assert len(warnings) == 1
    assert "정책 시행 상태 검토 필요" in html
    assert warnings[0] in html
    assert 'data-object-id="MC1"' in html


def test_mixed_policy_status_warning():
    data = {
        "discovery_summary": "Test",
        "policy_actions": [
            {
                "id": "PA10",
                "action": "전담검사 확대 및 수사부 추가 설치",
                "status": "IN_EFFECT",
                "responsible_actors": ["검찰청"],
                "affected_groups": ["수사기관"],
                "dependencies": [],
                "provenance": {
                    "page": 6,
                    "excerpt": (
                        "전담검사(23→43명)확대(9.2)확대완료..."
                        "지역거점검찰청등에여성·아동범죄수사부"
                        "추가설치(12→24곳)추진중"
    ),
               },
            }
        ],
        "material_changes": [],
        "reporting_leads": [],
        "follow_ups": [],
        "perspectives": [],
        "reporting_actions": [],
        "limitations": [],
    }

    analysis = ReportingAnalysis.model_validate(data)
    warnings = find_status_warnings(analysis)

    assert any("PA10" in warning for warning in warnings)
