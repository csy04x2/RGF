from .pdf import extract_pdf
from .models import SourceStructure,ReportingAnalysis
from .prompts import runtime_prompt
from .validation import validate_integrity,validate_preservation,normalize_related_descriptions
class Pipeline:
    def __init__(self,client): self.client=client
    def run(self,pdf_path):
        source=extract_pdf(pdf_path)
        structured=self.client.parse(runtime_prompt('source',source_material=source),SourceStructure)
        sj=structured.model_dump_json(indent=2)
        analysis=self.client.parse(runtime_prompt('discovery',source_material=source,structured_source_analysis=sj),ReportingAnalysis)
        normalize_related_descriptions(analysis)
        validate_integrity(analysis)
        validated=self.client.parse(runtime_prompt('validator',source_material=source,structured_source_analysis=sj,reporting_analysis=analysis.model_dump_json(indent=2)),ReportingAnalysis)
        normalize_related_descriptions(validated)
        validate_preservation(analysis,validated); validate_integrity(validated)
        return structured,validated
