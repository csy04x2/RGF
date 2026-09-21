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
