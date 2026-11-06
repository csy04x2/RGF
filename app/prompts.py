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
===== 기자용 분석 문체 =====
모든 분석 설명은 쉬운 한국어로, 핵심 결론과 취재 가치가 가장 높은 내용부터 작성한다.
장문의 보고서 대신 빠르게 훑어볼 수 있는 개조식·핵심 중심 문체를 쓴다.
한 문장 또는 한 항목에는 하나의 핵심 정보만 담고, 짧은 문장이나 명사형 구문을 사용한다.
여러 항목은 기존 문자열 필드 안에서 줄바꿈과 '- ' 글머리표로 구분한다.
추상적 표현, 불필요한 수식어, 중복 설명과 과도한 배경 설명을 줄인다.
'~라는 점에서 의미가 있으며', '~할 필요성이 존재한다', '~에 대한 검토가 요구된다'는 피한다.
각 취재 아이디어는 왜 중요한가 → 무엇이 아직 확인되지 않았는가 → 기자가 무엇을 확인해야 하는가를 분명하게 드러낸다.
why_it_matters에는 중요성, unknown에는 미확인 사항, reporting_question과 evidence_needed에는 추가 취재 방향을 담는다.
정책 발표 내용(source_signal), 미확인 사항, 추가 취재 방향을 섞어 쓰지 않는다.
취재 질문은 지나치게 축약하지 않고 구체적인 의문문으로 작성한다.
핵심 수치, 날짜, 적용 대상, 시행 조건, 법적 구분과 불확실성은 생략하지 않는다.
근거 없는 중요도 평가나 사실을 만들어내지 않는다. 정책 상태와 출처를 왜곡하지 않는다.
JSON 스키마와 기존 필드를 유지한다. HTML을 문자열에 삽입하지 않는다.
related_items의 유효한 참조 ID는 내용상 관련성이 입증됐다는 의미가 아니다.
""")
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
