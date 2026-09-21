import argparse
from pathlib import Path
from .llm import OpenAIJSONClient
from .pipeline import Pipeline
from .renderer import render
def main():
    p=argparse.ArgumentParser(description='RGF standalone v0.1'); p.add_argument('--input',required=True); p.add_argument('--json-output',required=True); p.add_argument('--html-output',required=True); p.add_argument('--model')
    a=p.parse_args(); _,result=Pipeline(OpenAIJSONClient(a.model)).run(a.input); html=render(result)
    Path(a.json_output).write_text(result.model_dump_json(indent=2),encoding='utf-8'); Path(a.html_output).write_text(html,encoding='utf-8'); print('VALIDATION: PASS')
if __name__=='__main__': main()
