import pytest
from app.pipeline import Pipeline
from app.models import SourceStructure
from tests.test_core import source_data,analysis_data
class MockClient:
    def parse(self,prompt,schema): return schema.model_validate(source_data() if schema is SourceStructure else analysis_data())
def test_mock_pipeline(monkeypatch):
    monkeypatch.setattr('app.pipeline.extract_pdf',lambda p:'[SOURCE PAGE 1]\ntext')
    s,a=Pipeline(MockClient()).run('x.pdf'); assert s.source_context.id=='SC1' and a.reporting_leads[0].lead_id=='RL1'
class BadClient:
    def parse(self,prompt,schema): raise ValueError('malformed')
def test_malformed_response(monkeypatch):
    monkeypatch.setattr('app.pipeline.extract_pdf',lambda p:'x')
    with pytest.raises(ValueError,match='malformed'): Pipeline(BadClient()).run('x')

def test_pipeline_normalizes_both_ai_responses(monkeypatch):
    from app.validation import validate_integrity
    monkeypatch.setattr('app.pipeline.extract_pdf', lambda p: 'source')

    class ParaphraseClient:
        def __init__(self):
            self.prompts = []

        def parse(self, prompt, schema):
            self.prompts.append(prompt)
            if schema is SourceStructure:
                return schema.model_validate(source_data())
            data = analysis_data()
            data['reporting_leads'][0]['related_items'] = [
                {'type': 'policy_action', 'id': 'PA1', 'description': 'paraphrase'},
                {'type': 'material_change', 'id': 'MC1', 'description': 'paraphrase'},
            ]
            if len(self.prompts) == 3:
                # The final label must follow the validator's current object.
                data['policy_actions'][0]['action'] = 'validator action'
                data['material_changes'][0]['change'] = 'validator change'
                assert '"description": "a"' in prompt
                assert '"description": "c"' in prompt
            return schema.model_validate(data)

    client = ParaphraseClient()
    _, result = Pipeline(client).run('unused.pdf')
    assert len(client.prompts) == 3
    assert [r.description for r in result.reporting_leads[0].related_items] == [
        'validator action', 'validator change'
    ]
    validate_integrity(result)

@pytest.mark.parametrize('invalid_stage', [2, 3])
def test_pipeline_rejects_invalid_reference_at_either_stage(monkeypatch, invalid_stage):
    from app.validation import IntegrityError
    monkeypatch.setattr('app.pipeline.extract_pdf', lambda p: 'source')

    class InvalidClient:
        calls = 0

        def parse(self, prompt, schema):
            self.calls += 1
            if schema is SourceStructure:
                return schema.model_validate(source_data())
            data = analysis_data()
            if self.calls == invalid_stage:
                data['reporting_leads'][0]['related_items'][0]['id'] = 'MC1'
            return schema.model_validate(data)

    client = InvalidClient()
    with pytest.raises(IntegrityError, match='wrong-type'):
        Pipeline(client).run('unused.pdf')
    assert client.calls == invalid_stage
