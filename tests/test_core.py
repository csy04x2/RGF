import json
import pytest
from pathlib import Path
from pydantic import ValidationError
from app.models import *
from app.validation import *
from app.renderer import render
from app.prompts import load_prompt
from app.llm import OpenAIJSONClient
def prov(): return {'page':1,'section':'s','excerpt':'e','source_basis':'b'}
def source_data(): return {'source_context':{'id':'SC1','title':'t','institutions':['i'],'date':'d','targets':['x'],'purpose':'p','provenance':prov()},'key_claims':[{'id':'KC1','claim':'c','type':'FACTUAL_NUMERICAL','evidence_in_source':['e'],'evidence_status':'SUPPORTED','provenance':prov()}],'material_changes':[],'source_gaps':[]}
def analysis_data(): return {'discovery_summary':'d','policy_actions':[{'id':'PA1','action':'a','status':'IN_EFFECT','responsible_actors':[],'deadline':None,'affected_groups':[],'dependencies':[],'provenance':prov()}],'material_changes':[{'id':'MC1','change':'c','before':'b','after':'a','affected_groups':[],'analytical_implication':'i','unknown':'u','provenance':prov()}],'reporting_leads':[{'lead_id':'RL1','priority':'A','lenses':['IMPLEMENTATION'],'related_items':[{'type':'policy_action','id':'PA1','description':'a'}],'source_signal':'s','material_implication':'i','unknown':'u','reporting_question':'q','why_it_matters':'w','evidence_needed':['e'],'targets':['t'],'provenance':prov()}],'follow_ups':[{'id':'FU1','related_lead_ids':['RL1'],'related_policy_action_ids':['PA1'],'promise':'p','responsible_actors':[],'target_date':None,'what_to_check':'w','completion_evidence':[],'operation_indicators':[],'follow_up_questions':[],'provenance':prov()}],'perspectives':[{'id':'P1','related_lead_ids':['RL1'],'target':'t','why_needed':'w','questions':[],'information_needed':[]}],'reporting_actions':[{'id':'RA1','related_lead_ids':['RL1'],'what_to_verify':'v','why_it_matters':'w','sources_or_contacts':[],'questions':[],'documents_or_data_to_request':[],'expected_evidence':['e'],'provenance':prov()}],'limitations':[{'id':'LIM1','type':'OTHER','description':'x'}]}
def test_models(): SourceStructure.model_validate(source_data()); ReportingAnalysis.model_validate(analysis_data())
def test_expected_evidence_string_rejected():
    d=analysis_data(); d['reporting_actions'][0]['expected_evidence']='bad'
    with pytest.raises(ValidationError): ReportingAnalysis.model_validate(d)
def test_integrity_duplicate():
    d=analysis_data(); d['limitations'][0]['id']='PA1'
    with pytest.raises(IntegrityError): validate_integrity(ReportingAnalysis.model_validate(d))
def test_dangling_and_wrong_type():
    d=analysis_data(); d['follow_ups'][0]['related_policy_action_ids']=['MC1']
    with pytest.raises(IntegrityError): validate_integrity(ReportingAnalysis.model_validate(d))
def test_preservation():
    a=ReportingAnalysis.model_validate(analysis_data()); b=ReportingAnalysis.model_validate(analysis_data()); validate_preservation(a,b); b.limitations=[]
    with pytest.raises(IntegrityError): validate_preservation(a,b)
def test_renderer_preserves():
    a=ReportingAnalysis.model_validate(analysis_data()); h=render(a)
    for ids in snapshot(a).values():
        for i in ids: assert f'data-object-id="{i}"' in h
    assert h.count('data-object-id=')==sum(map(len,snapshot(a).values()))
def test_prompt_loading(): assert load_prompt('source').strip()
def test_api_key_absent(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with pytest.raises(RuntimeError): OpenAIJSONClient('x')
def test_schema_sync():
    assert json.loads(Path('schemas/source-structure.schema.json').read_text(encoding='utf8'))==SourceStructure.model_json_schema()
    assert json.loads(Path('schemas/reporting-analysis.schema.json').read_text(encoding='utf8'))==ReportingAnalysis.model_json_schema()

def test_normalize_changes_only_reference_descriptions():
    data = analysis_data()
    data['reporting_leads'][0]['related_items'] = [
        {'type': 'policy_action', 'id': 'PA1', 'description': 'AI paraphrase'},
        {'type': 'material_change', 'id': 'MC1', 'description': 'another paraphrase'},
        {'type': 'source_claim', 'id': None, 'description': 'original claim'},
    ]
    analysis = ReportingAnalysis.model_validate(data)
    expected = analysis.model_dump()
    expected['reporting_leads'][0]['related_items'][0]['description'] = 'a'
    expected['reporting_leads'][0]['related_items'][1]['description'] = 'c'
    normalize_related_descriptions(analysis)
    assert analysis.model_dump() == expected
    validate_integrity(analysis)

@pytest.mark.parametrize('kind,ref', [
    ('policy_action', 'missing'), ('policy_action', 'MC1'),
    ('material_change', 'PA1'), ('material_change', 'missing'),
    ('source_claim', 'PA1'),
])
def test_normalize_rejects_bad_references_without_mutation(kind, ref):
    data = analysis_data()
    data['reporting_leads'][0]['related_items'].append(
        {'type': kind, 'id': ref, 'description': 'invalid'}
    )
    data['reporting_leads'][0]['related_items'][0]['description'] = 'paraphrase'
    analysis = ReportingAnalysis.model_validate(data)
    before = analysis.model_dump()
    with pytest.raises(IntegrityError):
        normalize_related_descriptions(analysis)
    assert analysis.model_dump() == before

@pytest.mark.parametrize('same_collection', [True, False])
def test_normalize_rejects_duplicate_ids(same_collection):
    data = analysis_data()
    if same_collection:
        data['policy_actions'].append(dict(data['policy_actions'][0]))
    else:
        data['limitations'][0]['id'] = 'PA1'
    analysis = ReportingAnalysis.model_validate(data)
    with pytest.raises(IntegrityError, match='duplicate ID'):
        normalize_related_descriptions(analysis)

def test_unknown_related_type_rejected():
    data = analysis_data()
    data['reporting_leads'][0]['related_items'][0]['type'] = 'unknown'
    with pytest.raises(ValidationError):
        ReportingAnalysis.model_validate(data)

def test_strict_integrity_still_rejects_description_mismatch():
    data = analysis_data()
    data['reporting_leads'][0]['related_items'][0]['description'] = 'paraphrase'
    with pytest.raises(IntegrityError, match='description mismatch'):
        validate_integrity(ReportingAnalysis.model_validate(data))

def test_report_summary_preserves_bullets_and_escapes_html():
    data = analysis_data()
    data['discovery_summary'] = '- 핵심 결론\n- <script>alert(1)</script>'
    html = render(ReportingAnalysis.model_validate(data))
    assert '- 핵심 결론\n- &lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert '<script>alert(1)</script>' not in html
    assert 'white-space:pre-wrap;overflow-wrap:anywhere' in html
