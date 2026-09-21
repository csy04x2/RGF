import json
from pathlib import Path
from .models import SourceStructure,ReportingAnalysis
ROOT=Path(__file__).resolve().parents[1]
def write_schemas():
    out=ROOT/'schemas'; out.mkdir(exist_ok=True)
    for name,model in [('source-structure.schema.json',SourceStructure),('reporting-analysis.schema.json',ReportingAnalysis)]:
        (out/name).write_text(json.dumps(model.model_json_schema(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
