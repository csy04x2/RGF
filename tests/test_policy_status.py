
import pytest
from pydantic import ValidationError

from app.models import MaterialChange
from app.prompts import runtime_prompt


def make_change(status):
    return {
        "id": "MC1",
        "change": "24-hour removal deadline",
        "before": "No specified deadline",
        "after": "24-hour deadline proposed",
        "implementation_status": status,
        "affected_groups": [],
        "analytical_implication": "Implementation requires verification",
        "unknown": "Actual enforcement date",
        "provenance": {
            "page": 11,
            "section": "Platform responsibility",
            "excerpt": "24-hour deadline",
            "source_basis": "Policy document",
        },
    }


def test_legislation_required_status():
    change = MaterialChange.model_validate(
        make_change("LEGISLATION_REQUIRED")
    )
    assert change.implementation_status == "LEGISLATION_REQUIRED"


def test_unknown_status_rejected():
    with pytest.raises(ValidationError):
        MaterialChange.model_validate(
            make_change("ALREADY_COMPLETED")
        )


def test_legacy_result_defaults_to_unknown():
    data = make_change("UNKNOWN")
    del data["implementation_status"]

    change = MaterialChange.model_validate(data)
    assert change.implementation_status == "UNKNOWN"


def test_discovery_prompt_contains_status_rules():
    prompt = runtime_prompt("discovery", source_material="test")

    assert "POLICY IMPLEMENTATION STATUS RULES" in prompt
    assert "LEGISLATION_REQUIRED" in prompt
    assert "UNKNOWN" in prompt


def test_validator_prompt_contains_status_rules():
    prompt = runtime_prompt("validator", source_material="test")

    assert "Recheck implementation_status" in prompt
    assert "Preserve object IDs" in prompt
