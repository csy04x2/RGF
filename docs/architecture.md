# Architecture

다음은 standalone v0.1의 canonical 방향이며, 현재 구현된 pipeline은 아니다.

```text
PDF Upload
↓
SOURCE INGESTION
↓
LLM STEP 1 — 자료 구조화
↓
Structured JSON
↓
LLM STEP 2 — 취재 분석
↓
Strict JSON
↓
INTEGRITY / VALIDATION ENGINE
↓
Validated JSON
↓
DETERMINISTIC RENDERER
↓
Reporting Brief
```

## 책임 경계

AI가 담당하는 것:

- source meaning 이해
- 중요한 변화 발견
- reporting gap 발견
- reporting implication 판단
- reporting question 생성
- 필요한 evidence 식별
- 필요한 경우 semantic relationship 판단

Deterministic code가 담당하는 것:

- JSON Schema validation
- required fields
- enum validation
- duplicate ID detection
- referenced ID existence
- reference type validation
- object count
- object preservation
- deterministic rendering
- renderer information-loss detection

## Relationship integrity

Stable ID는 display label이 아니라 **FOREIGN KEY**처럼 취급한다.

- **L1 — Referential Integrity:** 참조 ID가 실제 존재하는가.
- **L2 — Type Integrity:** 참조 ID가 올바른 object type을 가리키는가.
- **L3 — Semantic Relationship Integrity:** 두 object가 단순히 같은 주제인 것이 아니라 실제로 직접적인 기능 관계가 있는가.

L3가 존재한다는 이유만으로 지금 별도 semantic validator agent를 만들지 않는다. 먼저 generation structure와 deterministic validation을 구축하고, 실제 benchmark에서 residual L3 failure를 확인한 뒤 semantic validation layer가 필요한지 결정한다.

## Deterministic renderer contract

Validated JSON → deterministic template → HTML

Validated canonical JSON을 Reporting Brief로 표현한다. Renderer는 분석기가 아니다.

Renderer가 해서는 안 되는 것:

- 새로운 Reporting Lead 생성
- 기존 Reporting Lead 삭제
- 일부 object만 중요하다고 선택
- canonical JSON을 요약하여 정보 삭제
- 새로운 사실 추가
- 새로운 취재 판단 추가
- priority 재평가
- relationship 재해석

**1 JSON object = 1 deterministic UI component**

시각적 compression은 허용한다. 예를 들어 Reporting Lead의 핵심 내용을 보여주고 상세 분석, 필요한 증거, 원문 근거 보기를 펼침 영역에 둘 수 있다. 하지만 semantic information deletion은 허용하지 않는다.

현재는 책임과 계약만 보존한다. Framework, frontend/backend 분리, API, database, LLM provider, deployment 및 추가 infrastructure는 결정하지 않는다. Schema, validator, renderer와 application 구현은 이후 단계에서 진행한다.
