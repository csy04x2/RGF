from .models import ReportingAnalysis,COLLECTIONS,object_id
class IntegrityError(ValueError): pass
def snapshot(a): return {c:[object_id(x) for x in getattr(a,c)] for c in COLLECTIONS}
def validate_integrity(a:ReportingAnalysis):
    registries={c:{object_id(x) for x in getattr(a,c)} for c in COLLECTIONS}; all_ids=[]
    for ids in registries.values(): all_ids.extend(ids)
    if len(all_ids)!=len(set(all_ids)): raise IntegrityError('duplicate ID')
    pa,mc,rl=registries['policy_actions'],registries['material_changes'],registries['reporting_leads']
    for lead in a.reporting_leads:
        for r in lead.related_items:
            if r.type=='source_claim':
                if r.id is not None: raise IntegrityError('source_claim id must be null')
            elif r.type=='policy_action':
                if r.id not in pa: raise IntegrityError('dangling/wrong-type policy_action reference')
                target=next(x for x in a.policy_actions if x.id==r.id)
                if r.description!=target.action: raise IntegrityError('policy_action description mismatch')
            elif r.type=='material_change':
                if r.id not in mc: raise IntegrityError('dangling/wrong-type material_change reference')
                target=next(x for x in a.material_changes if x.id==r.id)
                if r.description!=target.change: raise IntegrityError('material_change description mismatch')
    for x in a.follow_ups:
        if not set(x.related_lead_ids)<=rl or not set(x.related_policy_action_ids)<=pa: raise IntegrityError('dangling/wrong-type follow-up reference')
    for x in [*a.perspectives,*a.reporting_actions]:
        if not set(x.related_lead_ids)<=rl: raise IntegrityError('dangling/wrong-type lead reference')
    return snapshot(a)
def validate_preservation(before,after):
    if snapshot(before)!=snapshot(after): raise IntegrityError('validator changed object IDs or counts')
