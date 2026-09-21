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
