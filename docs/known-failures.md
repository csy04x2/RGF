# Known regression failures

아래는 향후 regression에서 보호할 실패 범주다. 현재 실행 가능한 테스트나 실제 benchmark fixture는 없다. PA/MC/RL 등 표기는 전달받은 실패 설명을 보존한 것이며 schema 세부사항을 확정하지 않는다.

## A. Renderer deletion

Upstream canonical JSON에 N개의 object가 있는데 HTML에 일부만 렌더링됨. **FAIL.**

## B. Dangling reference

존재하지 않는 ID를 참조함. **FAIL.**

## C. Wrong-type reference

PA가 필요한 곳에서 MC/RL 등 잘못된 type을 참조함. **FAIL.**

## D. Semantic relationship mismatch

두 object가 같은 넓은 주제를 다루지만 직접적인 기능 관계가 없음. 예를 들어 어떤 Follow-up이 RL의 reporting_question을 직접 answer/update/test/revisit하지 않는데도 연결됨. **FAIL.**

## E. ID-description mismatch

Reference ID는 특정 object를 가리키지만 description은 다른 내용을 설명함. **FAIL 또는 semantic review 대상.**

## F. Unsupported outcome

Source는 법정형 5년 → 7년 변경인데 analysis는 “실형 가능성이 높아졌다.”라고 결론 냄. Source가 실제 outcome을 뒷받침하지 않는다면 **FAIL.**

## G. Renderer invention

Canonical JSON에 없는 substantive reporting point를 renderer가 새로 생성함. **FAIL.**
