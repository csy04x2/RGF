from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROMPTS={'source':ROOT/'docs/legacy-opal/prompts/source-structuring-prompt.txt','discovery':ROOT/'docs/legacy-opal/prompts/reporting-discovery-prompt.txt','validator':ROOT/'docs/legacy-opal/prompts/final-evidence-validator-prompt.txt'}
def load_prompt(name):
    text=PROMPTS[name].read_text(encoding='utf-8')
    return text.replace('Once complete, call system_objective_fulfilled.','').replace('Once validation is complete, call system_objective_fulfilled.','')
def runtime_prompt(name,**inputs):
    base=load_prompt(name)
    parts=[base,'\n\n===== RGF STANDALONE RUNTIME INPUT =====']
    for k,v in inputs.items(): parts += [f'\n--- {k} ---\n{v}']
    parts += ['\nReturn only JSON matching the supplied structured-output schema.']
    return ''.join(parts)
