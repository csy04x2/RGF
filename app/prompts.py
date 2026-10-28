from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROMPTS={'source':ROOT/'docs/legacy-opal/prompts/source-structuring-prompt.txt','discovery':ROOT/'docs/legacy-opal/prompts/reporting-discovery-prompt.txt','validator':ROOT/'docs/legacy-opal/prompts/final-evidence-validator-prompt.txt'}
def load_prompt(name):
    text=PROMPTS[name].read_text(encoding='utf-8')
    return text.replace('Once complete, call system_objective_fulfilled.','').replace('Once validation is complete, call system_objective_fulfilled.','')



def runtime_prompt(name, **inputs):
    base = load_prompt(name)

    parts = [
        base,
        "\n\n===== RGF STANDALONE RUNTIME INPUT ====="
    ]

    if name == "discovery":
        parts.append("""
===== POLICY IMPLEMENTATION STATUS RULES =====

1. Distinguish implemented policies from proposed policies.
2. "추진", "검토", "계획", "예정", "개정 추진" do not
   mean a policy is in effect.
3. Use IN_EFFECT only when the source explicitly confirms
   implementation or legal effect.
4. Use LEGISLATION_REQUIRED when implementation depends
   on legislation not confirmed as completed.
5. Use PLANNED or ANNOUNCED for future plans.
6. Use UNKNOWN when implementation status is unclear.
7. Do not infer implementation because a deadline has passed.
8. In material_changes.after, distinguish actual changes
   from proposed or planned changes.
9. Never present a government promise as an accomplished result.
10. Interpret policy status as of the source document date.
""")

    if name == "validator":
        parts.append("""
===== POLICY IMPLEMENTATION STATUS VALIDATION =====

Recheck implementation_status against the source document.
If the schema uses a field named status, recheck that field.

Distinguish implemented policies, completed legislation,
future plans, and proposals requiring legislation.

Do not treat proposed measures as already implemented.
Do not infer implementation because a deadline has passed.

Check that material_changes.after does not describe
a planned change as an accomplished result.

Preserve object IDs and all existing relationships.
Preserve all valid reporting leads and evidence references.
If a status is unsupported, mark the uncertainty explicitly.
""")

    for key, value in inputs.items():
        parts.append(f"\n--- {key} ---\n{value}")

    parts.append(
        "\nReturn only JSON matching the supplied structured-output schema."
    )

    return "".join(parts)
