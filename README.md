# RGF — Reporting Gap Finder

RGF standalone v0.1은 공식 PDF에서 기자가 추가 취재할 Reporting Gap/Lead를 찾고 원문 근거와 취재 행동에 연결하는 핵심 엔진이다. 요약기·기사 자동작성기·자율 팩트체커가 아니다.

파이프라인: `PDF → Source Structuring → Reporting Discovery → Evidence Validation → deterministic integrity validation → canonical JSON → deterministic HTML`.

## Windows PowerShell 실행

```powershell
cd C:\Users\EZ\OneDrive\Documents\ChatGPT\RGF
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:OPENAI_API_KEY="여기에_API_키"
$env:OPENAI_MODEL="사용할_모델_ID"
python -m app.cli --input "C:\path\source.pdf" --json-output "C:\path\rgf-result.json" --html-output "C:\path\rgf-result.html"
pytest -q
```

`--model`로 이번 실행에 한해 `OPENAI_MODEL`을 덮어쓸 수 있다. 성공하면 CLI가 `VALIDATION: PASS`를 표시하고 지정한 위치에 canonical JSON과 HTML을 쓴다. 검증 오류가 발생하면 HTML을 생성하지 않는다.

## 환경과 비용

OpenAI API 사용료는 ChatGPT Plus 구독과 별도일 수 있다. 실제 분석에서는 입력 PDF의 추출 텍스트가 OpenAI API로 전송된다. `OPENAI_API_KEY`가 없으면 실제 분석은 실행되지 않지만 mock 기반 자동 테스트는 API 없이 실행된다. API key는 저장소에 저장하지 않는다.

v0.1은 텍스트 추출 가능한 PDF만 지원한다. 스캔 PDF에서 텍스트가 전혀 추출되지 않으면 한국어 오류를 반환하며 OCR은 수행하지 않는다. 사용자 PDF와 실행 결과는 저장소에 자동 저장하지 않는다.

## Contract와 검증

Pydantic이 canonical contract의 실행 권위이며 `schemas/source-structure.schema.json`, `schemas/reporting-analysis.schema.json`은 그 모델에서 생성된다. 테스트가 두 표현의 동기화를 검사한다. Stable ID는 foreign key처럼 다루며 L1(존재)과 L2(type)는 코드가 강제한다. L3(의미 관계)는 evidence-validation LLM이 점검하지만 deterministic code가 완전 검증했다고 주장하지 않는다.

Renderer는 Jinja2 기반이며 분석하지 않는다. 각 canonical object는 정확히 하나의 `data-object-id` HTML component로 렌더링되고, collection별 component 수와 모든 ID를 사후 검사한다.

Legacy Opal prompt 원본은 `docs/legacy-opal/prompts/`에서 runtime에 직접 읽으며 수정하지 않는다. Opal placeholder와 `system_objective_fulfilled` 지시는 runtime adapter가 처리하고 실제 입력을 prompt 뒤에 명시적으로 붙인다. Legacy baseline은 gold answer가 아니며 schema 권위로 사용하지 않는다.
