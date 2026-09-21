from pathlib import Path
from jinja2 import Environment,FileSystemLoader,select_autoescape
from .models import ReportingAnalysis,COLLECTIONS,object_id
from .validation import snapshot,IntegrityError
ENV=Environment(loader=FileSystemLoader(Path(__file__).parent/'templates'),autoescape=select_autoescape(['html']))
def render(a:ReportingAnalysis)->str:
    html=ENV.get_template('report.html.j2').render(a=a,collections=COLLECTIONS,object_id=object_id)
    for c,ids in snapshot(a).items():
        if html.count(f'data-collection="{c}"')!=len(ids): raise IntegrityError(f'renderer component count mismatch: {c}')
        for i in ids:
            if html.count(f'data-object-id="{i}"')!=1: raise IntegrityError(f'renderer ID preservation mismatch: {i}')
    return html
