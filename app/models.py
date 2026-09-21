from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict
class StrictModel(BaseModel): model_config=ConfigDict(extra='forbid')
class ClaimType(str,Enum):
    FACTUAL_NUMERICAL='FACTUAL_NUMERICAL'; CAUSAL='CAUSAL'; COMPARISON='COMPARISON'; FORECAST='FORECAST'; EVALUATIVE_PROMOTIONAL='EVALUATIVE_PROMOTIONAL'
class EvidenceStatus(str,Enum):
    SUPPORTED='SUPPORTED'; PARTIALLY_SUPPORTED='PARTIALLY_SUPPORTED'; ASSERTION_ONLY='ASSERTION_ONLY'
class GapType(str,Enum):
    BASELINE='BASELINE'; DENOMINATOR='DENOMINATOR'; DEFINITION='DEFINITION'; TIME='TIME'; EVIDENCE='EVIDENCE'; PERSPECTIVE='PERSPECTIVE'
class Provenance(StrictModel):
    page:str|int|None=None; section:str|None=None; excerpt:str|None=None; source_basis:str|None=None
class SourceContext(StrictModel):
    id:str='SC1'; title:str; institutions:list[str]; date:str; targets:list[str]; purpose:str; provenance:Provenance
class KeyClaim(StrictModel):
    id:str; claim:str; type:ClaimType; evidence_in_source:list[str]; evidence_status:EvidenceStatus; provenance:Provenance
class SourceChange(StrictModel):
    id:str; item:str; before:str; after:str; change:str; effective_date:str|None=None; provenance:Provenance
class SourceGap(StrictModel):
    id:str; related_id:str|None=None; gap_type:GapType; missing_information:str; why_it_matters:str; provenance:Provenance
class SourceStructure(StrictModel):
    source_context:SourceContext; key_claims:list[KeyClaim]; material_changes:list[SourceChange]; source_gaps:list[SourceGap]
Status=Literal['IN_EFFECT','ONGOING','PLANNED','LEGISLATION_REQUIRED','ANNOUNCED','UNKNOWN']
Priority=Literal['A','B','C']
Lens=Literal['IMPLEMENTATION','OUTCOME','MEASUREMENT','PROBLEM_RESPONSE_FIT','LEGAL_REGULATORY_BOUNDARY','AFFECTED_PARTY_PERSPECTIVE','ACCOUNTABILITY_FOLLOW_UP','INTERNAL_TENSION_DEPENDENCY','BURIED_SIGNIFICANCE']
LimitationType=Literal['SOURCE_INSUFFICIENCY','PROVENANCE_UNCERTAINTY','EXTERNAL_VERIFICATION_REQUIRED','OTHER']
class PolicyAction(StrictModel):
    id:str; action:str; status:Status; responsible_actors:list[str]; deadline:str|None=None; affected_groups:list[str]; dependencies:list[str]; provenance:Provenance
class MaterialChange(StrictModel):
    id:str; change:str; before:str; after:str; affected_groups:list[str]; analytical_implication:str; unknown:str; provenance:Provenance
class RelatedItem(StrictModel):
    type:Literal['policy_action','material_change','source_claim']; id:str|None=None; description:str
class ReportingLead(StrictModel):
    lead_id:str; priority:Priority; lenses:list[Lens]; related_items:list[RelatedItem]; source_signal:str; material_implication:str; unknown:str; reporting_question:str; why_it_matters:str; evidence_needed:list[str]; targets:list[str]; provenance:Provenance
class FollowUp(StrictModel):
    id:str; related_lead_ids:list[str]; related_policy_action_ids:list[str]; promise:str; responsible_actors:list[str]; target_date:str|None=None; what_to_check:str; completion_evidence:list[str]; operation_indicators:list[str]; follow_up_questions:list[str]; provenance:Provenance
class Perspective(StrictModel):
    id:str; related_lead_ids:list[str]; target:str; why_needed:str; questions:list[str]; information_needed:list[str]
class ReportingAction(StrictModel):
    id:str; related_lead_ids:list[str]; what_to_verify:str; why_it_matters:str; sources_or_contacts:list[str]; questions:list[str]; documents_or_data_to_request:list[str]; expected_evidence:list[str]; provenance:Provenance
class Limitation(StrictModel):
    id:str; type:LimitationType; description:str
class ReportingAnalysis(StrictModel):
    discovery_summary:str; policy_actions:list[PolicyAction]; material_changes:list[MaterialChange]; reporting_leads:list[ReportingLead]; follow_ups:list[FollowUp]; perspectives:list[Perspective]; reporting_actions:list[ReportingAction]; limitations:list[Limitation]
COLLECTIONS=('policy_actions','material_changes','reporting_leads','follow_ups','perspectives','reporting_actions','limitations')
def object_id(x): return getattr(x,'lead_id',None) or getattr(x,'id')
