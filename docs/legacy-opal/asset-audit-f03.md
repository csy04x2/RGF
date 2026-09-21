# Foundation-03 — Legacy Asset Independent Audit

## 1. 감사 범위와 제한

기준 commit: `a9fb2c917c0f981d8deab81950c1e0aae01d3cf8`. 시작 및 재개 시 main, origin/main 동일, working tree clean을 확인했다. 다음 약칭은 모두 repository 상대경로를 뜻한다.

| 약칭 | 감사 자산 |
|---|---|
| PDF | docs/legacy-opal/benchmark/deepfake-policy-source-2024-11.pdf |
| D | docs/legacy-opal/prompts/reporting-discovery-prompt.txt |
| V | docs/legacy-opal/prompts/final-evidence-validator-prompt.txt |
| J | docs/legacy-opal/baselines/opal-reporting-analysis-baseline.json |
| H1 | docs/legacy-opal/failures/generate-brief-verbatim-pre-dump.html |
| H2 | docs/legacy-opal/failures/generate-brief-pretty-lossy.html |

6개 자산의 SHA-256은 Foundation-02 기준과 모두 일치했다. 두 prompt와 JSON, HTML 전체를 읽고, PDF 22쪽 전체의 텍스트와 렌더링된 페이지를 확인했다. PDF 위치는 **파일 페이지 / 인쇄 쪽수**로 표기한다. 표지와 목차 다음부터 인쇄 쪽수가 시작하므로 파일 4쪽은 인쇄 2쪽이다. 텍스트 파일 근거는 1부터 시작하는 행 번호다.

Source-structuring prompt와 독립 validation output은 없다. H1의 텍스트가 어떤 입력에서 생성됐는지, 두 HTML의 정확한 실행 입력이 J였는지는 확인할 수 없다. 따라서 J와 HTML의 관찰 가능한 차이와 renderer가 그 차이를 만든 원인이라는 주장을 구별한다. 외부 조사·웹 검색·Opal URL 접속은 하지 않았다. JSON 구조 검사는 표준 라이브러리의 일회성 메모리 내 검사로 수행했으며, PDF에는 이미 설치된 읽기·렌더링 도구를 사용했다. 자산 통합, 구현, 원본 수정, dependency 설치는 하지 않았다.

## 2. 결론

- **BLOCKER 3개, FIX BEFORE IMPLEMENTATION 6개, DEFER 1개.** 아래 목록의 고유 finding 수이며 사례·영향받은 객체 수와 다르다.
- 전체 판정: **FAIL — legacy 자산을 그대로 실행 계약·정답·renderer로 채택할 수 없음.** 보존된 migration 자체의 실패를 뜻하지 않는다.
- 현재 자산을 그대로 전제한 standalone 구현 착수는 불가하다. 원문과 다른 일정·기관·적용 범위, 의미가 맞지 않는 관계 3개, H2의 객체 손실·ID 재사용·새 분석이 막는다. 다음 최소 교정 결정을 먼저 할 수는 있다.
- JSON syntax와 L1/L2는 정상이다. 발견된 문제를 ID 파손이나 모든 분석의 허위로 확대 해석하지 않는다. 질문 자체가 원문 밖의 답을 요구한다는 이유로 오류 처리하지 않았다.

## 3. 자산별 판정표

| 자산 | 판정 | 핵심 문제 | 구현 영향 |
|---|---|---|---|
| PDF | PASS WITH ISSUES | 73.6%와 별도 검거 수치 411/506의 모집단 관계가 설명되지 않음 | 수치의 분모를 임의 결합하면 안 됨 |
| D | PASS WITH ISSUES | scalar null 지시와 field별 타입의 불일치, 입력 간 사실 authority 미분리 | 생성 허용 범위 결정 필요 |
| V | PASS WITH ISSUES | 타입 계약을 외부의 original schema에 의존, 전체 객체 삭제 예외와 보존의 경계 불명확 | 보정 성공·실패 판정 범위 결정 필요 |
| J | FAIL | source fidelity, L3 관계, 배열 타입, provenance 문제 | gold answer나 검증 완료 데이터로 사용 불가 |
| H1 | FAIL | reporting_analysis라는 표제와 실제 구조화 서술의 불일치; source 대조 오류 | baseline renderer 결과로 재사용 불가 |
| H2 | FAIL | 대량 누락, ID 의미 교체, 새 질문·판단 | renderer template로 재사용 불가 |

## 4. Discovery prompt 감사

실제 contract는 D388–522의 top-level 8개 field다. `discovery_summary`는 문자열, 나머지 7개는 객체 배열이다. PA는 action/status/actors/deadline/groups/dependencies/provenance, MC는 change/before/after/groups/analytical_implication/unknown/provenance, RL은 priority/lenses/related_items/source_signal/material_implication/unknown/reporting_question/why_it_matters/evidence_needed/targets/provenance를 요구한다. FU는 promise/actors/target_date/check/evidence/indicators/questions 및 두 관계 배열, P는 target/why/questions/information 및 RL 관계, RA는 verification/why/contacts/questions/requested materials/expected_evidence/provenance 및 RL 관계, LIM은 type/description을 요구한다. 각 객체의 id 또는 lead_id도 필수다. 이는 기존 지시의 독해이며 새 schema가 아니다.

PA/MC/RL/FU/P/RA의 순차 ID, 유일성, PA/MC 확정 후 참조, PA/MC description의 exact equality, source_claim의 null ID, RL 및 PA를 가리키는 downstream 배열이 명시돼 있다(D130–135, 166–170, 258–313, 333–363, 534). LIM1 예시는 있으나 LIM 순차 생성 설명은 별도로 없다. 현재 baseline에는 그로 인한 충돌이 없다.

Status 6개, priority A/B/C, lens 9개, related_items.type 3개, limitation.type 4개를 열거한다. Provenance는 PA/MC/RL/FU/RA에 요구하고 정확히 모르면 해당 값을 null로 둔다(D369–382). 관측 사실·분석·unknown 분리, 비언급을 부재로 바꾸지 않기, 발표를 실행으로 추정하지 않기는 일관적이다. 생성 단계여서 사전 object count 보존 의무는 없다.

직접적인 내부 모호성은 D535의 모든 unsupported scalar에 null을 쓰라는 지시와 D405 등의 non-null enum/string 표현이다(**FIX-03**). Field별 null 허용 표기와 포괄 final rule 중 무엇이 우선인지 정해져 있지 않다. D57–62는 supplied inputs 전체를 사실 근거로 인정하지만 원문과 구조화 해석의 authority 순서를 지정하지 않는다(**FIX-05**). 사실판단 실패를 자동으로 확정하는 규칙은 아니지만, 그대로 옮기기 전에 해결할 계약 차이다. Prompt 자체에 즉시 실행 불가능하다고 단정할 BLOCKER는 없다.

Deterministic 검사가 가능한 규칙: JSON syntax, key/타입/enum, ID 유일성·형식, 참조 존재·대상 type, description exact equality, null/배열 존재. 의미 판단이 필요한 규칙: source grounding, 중요성·중복 주제 여부, 분석과 사실의 구분, 외부 전제, L3 직접 기능 관계, excerpt의 의미 충실성. Opal 입력 placeholder와 마지막 system_objective_fulfilled 호출은 legacy 실행 문맥이며 현재 standalone 호출 가능성을 검증한 것은 아니다.

## 5. Validator prompt 감사

V40–60은 원문 > 구조화 해석 > 분석의 authority를 명시한다. 구조화 해석은 독립 근거가 아니며, 원문이 지지하지 않는 주장을 근거로 쓰지 말라고 한다. 따라서 **validator 자체가 없는 구조화 결과를 factual authority로 허용한다는 증거는 없다.**

V68–86, 396–398은 새 PA/MC/RL/FU/P/RA와 limitation 생성을 금지하고 valid text의 스타일 변경·편집적 priority 변경을 금지한다. V417–419는 기존 ID 유지·renumber 금지다. V92–143은 unsupported premise를 KEEP/ABSTRACT/REMOVE로 다루며, 유용한 질문은 보존한다. V336–354는 L1/L2/L3 실패 시 참조만 제거하고 대체 ID를 추측하지 않으며, provenance는 근거 없는 값만 null로 바꾼다(V360–376, 569–570).

“SAME reporting analysis”는 byte identity가 아니라 유효한 발견의 최대 보존을 뜻한다(V16, 545–576). 최소 수정 권한과 그 표현 자체는 충돌하지 않는다. 다만 전체 객체 삭제를 최후 수단으로 허용(V86)하면서 모든 existing object의 stable ID 유지를 요구(V417)하므로, 삭제 가능한 조건과 보존 대상의 범위가 명확하지 않다. **절대 object count 보존 규칙은 없다.** 삭제가 모두 금지됐다고 읽으면 안 된다.

V421–513은 required key 목록을 주지만 타입·enum·null 허용의 전체 정의는 주지 않는다. V527은 original schema를 참조하나 입력에는 reporting_analysis와 두 source 입력만 있다. 그래서 J의 expected_evidence 문자열 같은 입력 타입 오류를 이 prompt의 key 목록만으로 확정적으로 교정할 수 없다. 이 계약 의존성과 삭제 예외를 **FIX-04**로 묶었다. 실제 validator output이 없어 그것이 오류를 생성했거나 보존했다고 단정하지 않는다.

L1/L2·key 복구 등 기계적 검사와 unsupported premise·L3 등 의미 판단이 한 prompt에 섞여 있다. 혼합 자체를 실패나 별도 agent 필요성으로 판정하지 않았다.

## 6. Baseline JSON 구조 감사

JSON parsing 성공. 최상위 field: `discovery_summary`, `policy_actions`, `material_changes`, `reporting_leads`, `follow_ups`, `perspectives`, `reporting_actions`, `limitations`.

| Collection | 객체 수 | 모든 객체 ID |
|---|---:|---|
| policy_actions | 5 | PA1, PA2, PA3, PA4, PA5 |
| material_changes | 2 | MC1, MC2 |
| reporting_leads | 3 | RL1, RL2, RL3 |
| follow_ups | 2 | FU1, FU2 |
| perspectives | 2 | P1, P2 |
| reporting_actions | 2 | RA1, RA2 |
| limitations | 2 | LIM1, LIM2 |
| 합계 | **18** | 고유 ID 18개 |

Duplicate ID **0**, ID 형식·순번 오류 **0**, dangling reference **0**, wrong-type reference **0**. 실제 non-null 참조는 **11개**다. RL.related_items에서 PA3·PA4 각 1개, FU.related_lead_ids 2개, FU.related_policy_action_ids 2개, P.related_lead_ids 3개, RA.related_lead_ids 2개다. RL3의 source_claim.id=null은 정상 예외이며 dangling으로 세지 않았다. PA/MC description exact mismatch **0/2**.

Required key 누락 **0**, 예상 밖 key **0**(nested provenance/related_items 포함). 명시된 field별 null 위반 **0**. Null은 **15개**: provenance.page 14개, RL3.source_claim.id 1개. Page가 null인 것 자체는 허용되지만 모두 비어 있어 trace가 약하다. **타입 불일치 2개**: RA1.expected_evidence(J254), RA2.expected_evidence(J270)가 문자열이다. D506은 문자열 배열을 요구한다(**FIX-01**). 다른 검사 대상 타입 오류는 0이다.

실제 enum 분포:

- PA.status: IN_EFFECT 2, ONGOING 1, PLANNED 2; 나머지 후보 0.
- RL.priority: A 2, B 1, C 0.
- RL.lenses: LEGAL_REGULATORY_BOUNDARY 2, IMPLEMENTATION 1, PROBLEM_RESPONSE_FIT 1, MEASUREMENT 1, AFFECTED_PARTY_PERSPECTIVE 1; 나머지 0.
- related_items.type: policy_action 2, source_claim 1, material_change 0.
- LIM.type: EXTERNAL_VERIFICATION_REQUIRED 1, SOURCE_INSUFFICIENCY 1; 나머지 0. Enum 밖 값 **0**.

입력 배열의 항목 수도 전수 확인했다. 아래 숫자는 객체 순서에 대응한다.

| Collection | 내부 배열별 길이 |
|---|---|
| PA1–5 | responsible_actors 2/1/2/2/1; affected_groups 1/1/1/2/1; dependencies 2/1/1/1/1 |
| MC1–2 | affected_groups 2/1 |
| RL1–3 | lenses 각 2; related_items 각 1; evidence_needed 각 3; targets 각 3 |
| FU1–2 | related_lead_ids 각 1; related_policy_action_ids 각 1; responsible_actors 1/2; completion_evidence 각 2; operation_indicators 각 2; follow_up_questions 각 1 |
| P1–2 | related_lead_ids 2/1; questions 각 2; information_needed 각 2 |
| RA1–2 | related_lead_ids 각 1; sources_or_contacts 각 2; questions 각 2; documents_or_data_to_request 각 2; expected_evidence는 둘 다 배열 아님 |

Incoming reference가 없는 객체는 **12개**: PA1, PA2, MC1, MC2, FU1, FU2, P1, P2, RA1, RA2, LIM1, LIM2. 그중 직접 참조 대상이 될 수 있는 PA/MC/RL에서는 PA1, PA2, MC1, MC2의 **4개**다. 전부 참조돼야 한다는 규칙이 없으므로 orphan 오류 **0**이다. FU/P/RA/LIM은 incoming edge가 없는 것이 정상일 수 있다.

ID를 제외한 완전 동일 객체 **0**. PA2–MC1, PA3–MC2는 같은 정책 소재를 action과 change로 다르게 표현한다. 이를 중복 오류로 세지 않았다.

**L3 의미 불일치 3/11개**(**BLOCKER-02**):

- FU2 → RL3(J210): 센터 24시간 운영·인력 점검은 청소년 처벌 억제 효과라는 RL3 질문을 직접 answer/update/test/revisit하지 않는다.
- RA2 → RL3(J264): 피해지원 센터 업무량 자료는 RL3의 제작 유인·억제 효과를 직접 검증하지 않는다.
- P1 → RL1(J230–234): 기술 탐지·워터마크 우회 질문은 RL1의 법적·외교적 집행 수단에 직접 증거를 제공하지 않는다. P1 → RL2는 기술 성능·오탐 관련성이 있어 유지 가능한 관계다.

FU2 → PA5는 같은 원스톱 지원체계의 운영이라는 직접 연관성이 있어 명백한 오류로 세지 않았다. 그렇다고 FU2의 잘못된 일정·적용 범위를 인정한 것은 아니다.

## 7. Baseline source fidelity 감사

판정 단위는 **ID 객체 18개**다. 별도로 문자열 discovery_summary 1개를 판정했다. 부분 지지가 있는 객체의 unsupported 세부 문장은 PARTIALLY SUPPORTED에 포함하고 중복 합산하지 않는다. SOURCE-SUPPORTED는 원문이 말한다는 뜻이며 외부 사실 검증 완료가 아니다. 모든 provenance의 인용 정확성은 아래 별도 항목에서 다뤘다.

| Collection | SOURCE-SUPPORTED | PARTIALLY SUPPORTED | UNSUPPORTED | NOT A SOURCE FACT — ANALYTICAL QUESTION | CANNOT VERIFY FROM AVAILABLE ASSET |
|---|---:|---:|---:|---:|---:|
| policy_actions | 0 | 5 | 0 | 0 | 0 |
| material_changes | 1 | 1 | 0 | 0 | 0 |
| reporting_leads | 0 | 3 | 0 | 0 | 0 |
| follow_ups | 0 | 2 | 0 | 0 | 0 |
| perspectives | 0 | 0 | 0 | 2 | 0 |
| reporting_actions | 0 | 1 | 0 | 1 | 0 |
| limitations | 1 | 0 | 0 | 1 | 0 |
| **18 객체 합계** | **2** | **12** | **0** | **4** | **0** |
| discovery_summary 별도 | 0 | 0 | 1 | 0 | 0 |
| **19 판정 단위 합계** | **2** | **12** | **1** | **4** | **0** |

MC1의 처벌 신설·금액은 PDF8/6, 19/17, 22/20에 근거한다. LIM2의 해당 실시간 자동화 계획에 대한 오탐지율·처리 용량 미제시는 원문 전체 확인 결과다. PDF9/7의 경찰 탐지 S/W 5–10분과 실적 246건은 별도 시스템으로서 위 두 성능 지표의 근거가 아니다. P1/P2/RA2/LIM1은 취재 질문·요청 또는 조건부 검증 필요로 읽는다. 답이나 효과가 이미 확정됐다는 진술로 오판하지 않는다.

### UNSUPPORTED 전수 목록

**discovery_summary(J2)**: 이 자료를 “2024년 9월 정부가 발표한” 방안이라고 확정한다. PDF 표지는 **2024년 11월**이다. 9월의 입법·우선조치와 이 문서의 발표 시점을 섞었다. 요약 전체가 모두 허위라는 뜻이 아니라, 문서 식별 전제에 명백한 오류가 있어 이 단위를 UNSUPPORTED로 판정했다(**BLOCKER-01**).

### PARTIALLY SUPPORTED 전수 목록

다음 12개 객체의 사실 오염 사례는 하나의 **BLOCKER-01** 아래 기록한다. 원문 미언급은 “원문으로 지지되지 않음”이며 실제 세계에서 거짓이라고 판정하지 않았다.

| 객체 / 근거 위치 | 지지되는 내용 | 지지되지 않거나 과장된 부분과 PDF 대조 |
|---|---|---|
| PA1 / J5–16 | 5→7년 상향, 10.16 공포 후 즉시 실행(PDF8/6,22/20) | 해당 개정의 담당은 법무부로 표시되는데 여성가족부를 공동 책임기관으로 추가. 여가부 담당 청소년성보호법과 구별 필요 |
| PA2 / J20–31 | 소지·구입·저장·시청 처벌 신설과 시행(PDF8/6,22/20) | dependencies의 “국무회의 의결”은 원문에 명시되지 않은 절차 전제. 일반 법률 지식으로 보충하지 않음 |
| PA3 / J35–46 | 플랫폼 의무 요구·미이행 시 제재(PDF11/9) | deadline “2024년 말까지” 대신 과제표는 “계속”(PDF20/18 ⑦). 담당은 방통위인데 여가부 추가. 청소년보호법이라는 법적 근거도 해당 항목 원문은 정보통신망법이며, 자율규제에만 의존했다는 source_basis는 대상·기간을 과도하게 일반화 |
| PA4 / J50–61 | AI 실시간 감지·삭제요청 자동화(PDF13/11) | “2025년 상반기” 대신 과제표는 “계속”; 담당은 여가부·과기부인데 방심위로 바꾸고 여가부 누락(PDF21/19 ⑮). R&D 예산 확보를 이 사업의 명시적 선행 dependency로 정한 근거도 없음 |
| PA5 / J65–76 | 1366 일원화·여가부·상담시간 확대(PDF14/12) | 2025년 4월은 지역센터 관련 법 시행(PDF15/13), 신고 일원화 기한은 ~2025(PDF21/19 ⑰). 상담 인력 교육을 이 과제의 명시적 dependency로 적은 근거 없음 |
| MC2 / J97–108 | 이전 협의 채널 부재(PDF19/17), 적극 법 해석과 의무 부과(PDF11/9) | 채널 부재와 “자율 규제 의존”을 동일한 이전 상태로 합침. after의 과태료는 의무 미이행이라는 조건을 생략. 국내 접속 차단을 이미 사용 가능한 수단으로 전제한 implication, 법적 규제 근거를 새로 “마련”했다는 source_basis도 원문의 기존 법 적극 해석보다 강함 |
| RL1 / J114–135 | 플랫폼 규제 계획은 source-supported | “서비스 차단 이외”라는 질문은 플랫폼 서비스 차단이 확보된 수단임을 전제. 원문은 게시자 서비스 이용중단 입법 추진과 불법물 삭제·차단을 말함(PDF11–12/9–10). why_it_matters의 “법 개정”은 해당 기존 법 해석과 혼동; 실효성 저하→불신 및 범죄 확산 한계는 검증 전 인과 추론 |
| RL2 / J139–160 | 자동화 계획과 오탐·구제절차를 묻는 질문은 타당한 분석 | why_it_matters의 기본권 우려 해소가 사회적 수용성을 “결정할 핵심 변수”가 될 것이라는 인과 확정은 원문 근거 없음. 오탐 가능성을 질문하는 것 자체를 오류 처리하지 않음 |
| RL3 / J164–185 | 73.6%·낮은 범죄 인식은 원문에 있음(PDF3–4/1–2) | 대책이 처벌에 집중된다는 전제는 원문의 4대 분야·교육 확대(PDF7/5,16/14)를 충분히 반영하지 않음. 교육·문화 병행 여부가 장기 성패를 “결정할 것”이라는 확정은 검증되지 않음 |
| FU1 / J191–205 | 의무 미이행 시 과태료 및 행정집행 후속 질문(PDF11/9) | “2024년 4분기” 기한 없음(과제표는 계속). 조건부 제재를 확정 부과 약속으로 바꿈. 국내대리인 지정만으로 과태료 집행 완료를 입증할 수 없음 |
| FU2 / J209–223 | 지역센터 17개 추진, 상담 24시간 확대 각각 존재(PDF14–15/12–13) | 두 항목과 법 시행일을 합쳐 “2025년 4월까지 전국 17개 전체 24시간 운영”이라는 단일 약속을 구성. 원문에는 그 결합된 완료 약속 없음 |
| RA1 / J247–259 | 과태료 집행 실효성 취재는 분석으로 가능 | “최근 해외 플랫폼을 대상으로 부과된 과태료”를 이미 존재하는 대상으로 전제. PDF11/9은 규제·조건부 제재 추진이며 구체적 과거 부과 사례나 통계의 존재를 입증하지 않음. 존재 여부를 묻는 별도 질문은 오류 아님 |

기관 연락 대상(targets/sources_or_contacts)은 취재 제안으로 읽었으며 모든 후보 기관이 이미 해당 정책을 집행했다는 사실 주장으로 바꾸지 않았다. 그러나 PA의 responsible_actors는 명시적 담당 사실이므로 따로 검증했다.

### Source excerpt mismatch와 source_basis

Provenance 객체는 14개다. 14개 excerpt 모두 PDF 추출문에서 공백만 제거한 연속 문자열과 일치하지 않았다. 실제 페이지도 대조했다. **14개 모두 허위 사실이라는 뜻은 아니다.** 대부분 축약·재서술이며, 인용 필드로 그대로 쓰기에는 정확하지 않다(**FIX-02**).

| 객체 | PDF 근거 | 관찰 |
|---|---|---|
| PA1 | 8/6,22/20 | 법정형 상향 문장을 제목 형태로 축약 |
| PA2, MC1 | 8/6,22/20 | 행위 처벌 신설을 “시청죄 신설”로 재서술; 숫자는 원문에 있음 |
| PA3, MC2, RL1, FU1, RA1 | 11/9 | 단계별 의무와 “미이행 시 과태료 등 제재”를 “시정명령 및 과태료 부과 추진”으로 결합 |
| PA4, RL2 | 13/11 | 실제 감지·발송·삭제여부 모니터링 설명을 짧게 바꿈 |
| PA5 | 14/12,15/13 | 일원화와 중앙·지역 24시간 확대를 합성한 인용 |
| RL3 | 4/2 | “피의자 10대 비중 73.6%”를 “피의자의 73.6%가 10대로 확인됨”으로 바꿈 |
| FU2 | 14–15/12–13 | 17개 설치와 24시간 운영을 하나의 구절로 합침 |
| RA2 | 14/12,18/16 | “인력 증원 및 전문성 강화”는 해당 원문 구절 그대로가 아님 |

Page는 14개 모두 null. Section은 PA2/RL3의 “현황 및 문제점” 2개만 원문의 표제와 문자열 일치하며, PA2의 처벌 신설 근거는 해당 배경 절보다 PDF8/6의 조치다. 나머지 12개도 임의의 요약 표제를 exact section으로 오인하지 않게 해야 한다. “피해자 보호 및 지원 강화” 등은 의미상 가까워도 실제 표제와 같지 않다.

Source_basis의 실질 과장은 PA3의 자율규제 전용 과거상태, MC2의 법적 근거 마련, FU2의 전국 상시화 범위에 있다. 이들은 BLOCKER-01의 같은 사례이므로 별도 finding으로 중복 집계하지 않았다. MC1의 “획기적”과 RA1/RA2의 “검증 필요/현실성 검토”는 분석적 표현으로서 source_basis와 분석의 경계를 흐리지만, 새 외부 사실이라고 단정하지 않는다.

이미 발생한 처벌·범죄 억제 outcome을 확정한 lead는 **0개**다. 다만 RL1–3에 위 표의 인과·미래 결과 과장이 있으므로 “unsupported outcome 0 = 모든 분석 정상”은 아니다.

### 원문 자체의 수치 관계

PDF4/2는 73.6%를 기재하면서 같은 페이지의 별도 사례 표에 검거 506명 중 10대 411명을 제시한다. 411/506은 약 **81.23%**다. 동일 모집단·시점이라고 설명돼 있지 않으므로 73.6%가 거짓이라고 결론 내리지 않는다. J의 73.6% 자체는 source-supported다. 두 수치를 같은 근거로 연결하는 것은 보류해야 한다(**DEFER-01**).

## 8. Prompt 간 contract 충돌

Top-level key 차이 0, object required key 차이 0, 추가 required field 0. 명시적인 enum 값·ID prefix·reference target type의 상반 규칙은 0이다. V가 enum/type 목록을 되풀이하지 않는 것은 서로 다른 enum을 요구한다는 뜻이 아니다. 유효 정보 보존과 불필요한 재발견 금지도 양립한다.

| Discovery의 실제 규칙 | Validator의 실제 규칙 | 충돌 여부 | 구현 영향 | 등급 |
|---|---|---|---|---|
| D535: unsupported scalar에는 null; field 표의 일부는 string/enum만 허용 | V527–528: original schema가 null을 허용할 때만 null | null 허용 지시의 범위가 불일치. D 자체의 field 표와 final rule도 긴장 | 같은 누락 근거를 생성 단계는 null 처리하고 검증 단계는 허용 여부를 판정하지 못할 수 있음 | FIX BEFORE IMPLEMENTATION, FIX-03 |
| D57–62: supplied inputs가 factual basis이며 그 입력이 확정한 것이 source-derived | V48–58,193–194: 원문만 최종 authority; 원문 미지지 구조화 주장 사용 금지 | 원문 미지지 구조화 주장의 수용 범위 차이. 필드명 충돌은 아님 | 생성 단계에서 승인된 factual premise가 검증 단계에서는 폐기 대상이 됨 | FIX BEFORE IMPLEMENTATION, FIX-05 |

V의 schema/type 의존과 삭제 예외는 V 자체의 문제(FIX-04)로 기록했으며 별도 prompt 간 충돌 수를 늘리지 않았다. 새 계약이나 prompt 수정안을 작성하지 않았다.

## 9. HTML 감사

### A. Verbatim/pre-dump HTML

H1에는 `<pre>`가 **2개**, baseline ID 표시는 **0개**다. SECTION 1은 reporting_analysis라고 쓰였지만 자료 개요, 핵심 주장 7개, 변화 5개, 기본 정보 공백 5개를 담은 서술형 자료 구조화 결과 형태다(H1 42–181). J의 8개 field·18개 객체를 그대로 dump한 것이 아니다. SECTION 2는 source_material이라는 이름 아래 Opal blob URL 하나만 있다(H1 188–191). PDF 본문은 포함하지 않는다.

- Object coverage: J의 stable ID 기준 식별 **0/18**. 정책 소재의 중첩은 있으나 입력 종류가 달라 J의 18개를 renderer가 삭제했다고 인과적으로 단정할 수 없다. H1의 실제 upstream 독립 파일이 없어 원래 텍스트 대비 verbatim 보존율은 **확인 불가**다.
- Component: 두 큰 pre 블록이며 1 JSON object = 1 component 구조가 아니다. 자료가 보인다는 사실과 deterministic object rendering은 별개다.
- Provenance: “본문 4쪽” 등 위치만 남고 원문 자체·정확한 excerpt·stable relationship은 없다. 파일 페이지 4를 본문 4로 쓰는 등 페이지 기준도 모호하다. Source/analysis는 주장·변화·공백의 제목으로 일부 구분하지만 신뢰 가능한 canonical 경계로 확인되지는 않는다.
- 관찰된 내용 오류: H1 58은 10,305건을 2024년 10월 기준이라고 쓰지만 PDF4/2 표의 해당 셀은 **9월 기준**이다. H1 63–66은 73.6%의 근거로 411/506을 직접 연결한다. H1 143은 삭제지원 주체 확대 시행을 10.16 즉시로 확정하지만 PDF8/6의 처벌 조치 즉시 실행 문구를 해당 법 전체에 전용할 수 없고 PDF15/13은 성폭력방지법 2025년 4월 시행을 명시한다. H1 172는 현재 인력 대비 증원 명수가 없다고 하지만 PDF11/9에 **12→26명, 18→33명**이 있다.
- 발명 여부: 위 부정확한 내용은 H1 안에 실제 존재한다. 다만 별도 upstream이 없어 **renderer가 새로 발명했는지, 입력 오류를 보존했는지는 확인 불가**다. H1 79의 국내사업소 부재 자체는 PDF5/3에 있으므로 외부 지식 발명으로 판정하지 않았다.

이 사례는 **FIX-06**이며 baseline renderer로 재사용 불가다. CSS 취향이나 pre 사용만으로 실패 판정한 것이 아니다.

### B. Pretty/lossy HTML

H2의 visible ID는 **PA1, PA2, RL1의 3개**다. 단순 ID 문자열 개수와 의미 보존 개수는 다르다.

| Collection | J 객체 | H2의 객체별 식별 | 누락·변경 |
|---|---:|---|---|
| policy_actions | 5 | 정책 주제 2개: J.PA2와 J.PA3에 대응 | PA1/PA4/PA5의 독립 객체 없음: 3개. 표시 ID는 PA1/PA2로 재배정 |
| material_changes | 2 | 0개 독립 객체 | 2개. 소지 처벌이라는 소재 중첩을 MC1 보존으로 세지 않음 |
| reporting_leads | 3 | baseline 질문에 대응하는 객체 0개 | 3개 모두 보존 안 됨. 표시 RL1은 새 질문 |
| follow_ups | 2 | 0개 | 2개 |
| perspectives | 2 | 0개 | 2개 |
| reporting_actions | 2 | 0개 | 2개 |
| limitations | 2 | 0개 식별 가능한 원 객체 | 2개 대신 일반 badge 3개 |

따라서 baseline 18개 중 **정책 주제 대응 2개**, 나머지 **16개는 독립 객체로 대응되지 않는다**. 이것은 완전 보존 2/18이라는 뜻이 아니다. J의 key/value/관계가 완전하게 보존된 객체는 **0/18**이다. H2에는 요약문으로 AI 등 다른 소재도 언급되므로 “그 주제의 단어조차 전혀 없다”는 의미로 누락 수를 사용하지 않는다.

변형과 발명(**BLOCKER-03**):

- H2 59–62의 PA1은 실제로 J.PA2의 소지·시청 처벌인데 IN_EFFECT를 **COMPLETED**로 바꿨다. “반포 목적 관계없이 소지·시청 처벌”은 PDF8/6의 편집·반포 조항 수식어를 소지·시청에 붙인 합성 인용이다.
- H2 67–70의 PA2는 J.PA3의 해외 플랫폼 규제 소재이며 ONGOING은 유지했지만 ID와 문구가 달라졌다. “접속 차단 검토”는 J.PA3의 excerpt에 없으며 원문의 게시물 삭제·차단과 플랫폼 전체 접속 차단을 구별하지 않는다.
- H2 82–96의 RL1은 priority A 표시는 같지만 J.RL1의 행정제재·법적 외교적 집행 질문을 **단체방 입장·고의성·자동 다운로드 면책** 질문으로 교체했다. Title도 새로 만들어졌다. 해당 새 질문이 합리적인 취재일 수 있는지와 renderer가 발명해도 되는지는 다른 문제다.
- H2 49는 “5가지 핵심 취재 경로”라고 하지만 J의 leads는 3개, HTML guide는 1개다. 숫자·출력 개수 모두 맞지 않는다.
- H2 108–110의 “재정적 근거 부족”, “법안 통과 불확실성”은 J.LIM1/2에 없는 별도 제한 판단이다. “외부 교차 확인 필요”라는 일반 문구는 두 limitation의 구체적 내용을 보존하지 않는다.
- PA의 actors/deadline/dependencies/affected_groups, RL의 related_items/source_signal/unknown 등 대부분 필드, FU/P/RA, 원래 evidence 요청과 관계 **11개 전부의 명시적 연결**이 사라졌다. Excerpt 모양의 짧은 텍스트가 2개 있어도 J의 provenance tuple을 보존한 것이 아니다. 접힘 영역에 원문 데이터를 숨겨 둔 흔적도 HTML에는 없다.

J 대비 deletion/invention은 파일 비교로 확인된다. 정확한 실행 입력 로그가 없어 H2 실행 당시 J가 입력이었다고 단정하거나, 전후 버전이 같은 모델 호출이라고 단정하지 않는다. 그래도 H2를 J의 보존 renderer로 사용할 수 없다는 결론은 달라지지 않는다.

## 10. 발견 사항 목록

같은 원인의 사례를 아래 고유 ID 하나에 묶었다. Source fidelity 개별 판정 수, HTML 차이 수, finding 수를 합산하지 않는다.

| ID | 등급 | 대상 | 실제 관찰 | 근거 위치 | 영향 | 가장 작은 다음 행동 |
|---|---|---|---|---|---|---|
| BLOCKER-01 | BLOCKER | J / PDF | 발표월 오류와 12개 부분 지지 객체의 담당·기한·조건·범위·전제 과장 | J2, PA1–5, MC2, RL1–3, FU1–2, RA1; §7의 PDF 위치 | 잘못된 취재 전제·약속·근거를 정답으로 고정 | §7의 사실 필드와 원문 대응을 검토해 향후 사용 시 교정·불확실 처리할 항목 확정; legacy 원본은 보존 |
| BLOCKER-02 | BLOCKER | J | L1/L2를 통과하지만 L3가 맞지 않는 3개 edge | J210,230–234,264; RL1 J127, RL3 J177 | 엉뚱한 lead의 근거 수집·후속 점검으로 연결 | 해당 세 관계의 제거 여부만 판정; 대체 ID를 추측하지 않기 |
| BLOCKER-03 | BLOCKER | H2 / J | 18개 중 완전 보존 0; ID 의미 교체와 새 질문·제한 판단 | H2 49,59–70,82–110; §9B | renderer의 의미 삭제·발명 | H2를 template에서 제외하고 관찰된 누락·변형을 향후 보존 검사의 기준으로 남기기 |
| FIX-01 | FIX BEFORE IMPLEMENTATION | J / D | expected_evidence 문자열 2개, 요구는 배열 | J254,270; D506 | 후속 배열 처리 계약 불일치 | 두 필드의 타입 처리를 구현 전에 결정 |
| FIX-02 | FIX BEFORE IMPLEMENTATION | J / PDF | 14개 excerpt가 축약·재서술, page 전부 null, section 대부분 원 표제 아님 | J의 provenance 14개; §7 인용 대조 | 요약을 직접 인용으로 오인하고 원문 추적 실패 | exact excerpt와 요약을 구별할 취급을 결정하고 사용 대상의 실제 페이지를 확인 |
| FIX-03 | FIX BEFORE IMPLEMENTATION | D / V | 포괄 null 지시와 field별 null 허용 범위가 불일치 | D405–460,535; V527–528 | 생성·검증의 허용값 판단 차이 | null 지시의 적용 범위와 우선순위만 확정 |
| FIX-04 | FIX BEFORE IMPLEMENTATION | V | original schema의 타입 정의가 입력 계약에 없고 전체 객체 삭제 예외가 불명확 | V86,404–419,421–528,545–576 | 잘못된 타입·복구 불가능 객체에 대한 보정 성공 기준 불명확 | 실제 참조할 계약 정보와 삭제/실패 처리 경계를 구현 전에 명시 |
| FIX-05 | FIX BEFORE IMPLEMENTATION | D / V | 구조화 해석을 factual input으로 보는 범위와 원문 authority 규칙의 차이 | D57–74; V40–60,193–200 | 입력 해석의 unsupported 사실이 discovery를 통과할 수 있음 | 두 단계의 factual authority 적용 범위를 일치시키는 결정만 수행 |
| FIX-06 | FIX BEFORE IMPLEMENTATION | H1 / PDF | baseline이 아닌 서술을 reporting_analysis로 표기; 기간·비율 근거·시행일·인력 공백 오류 | H1 42–181, 특히 58,65,143,172; PDF4/2,11/9,15/13 | 다른 artifact를 baseline의 무손실 렌더링으로 오인 | 실제 입력 종류를 구별하고 원 upstream이 없으면 보존율·발명 원인을 미확인으로 유지 |
| DEFER-01 | DEFER | PDF | 73.6%와 별도 411/506의 분모·기간 관계 미설명 | PDF4/2 | 서로 다른 통계를 동일 모집단으로 결합할 위험 | 외부 사실 보충 없이 원문 수치를 각각 보존; 이후 benchmark에서 비교 필요 시 모집단 확인 |

## 11. 다음 최소 행동

1. §7의 source fidelity 예외를 원문 위치별로 검토하여 향후 사용 시 교정하거나 불확실하게 둘 사실만 결정한다. Legacy 파일은 그대로 둔다.
2. L3 불일치 3개 관계와 expected_evidence 타입 2개의 처리 결정을 내린다.
3. Null 범위, factual authority, validator의 계약 참조·삭제 예외만 명확히 한다. 이번 감사에서 새 schema나 prompt를 만들지는 않는다.
4. 인용·페이지 대응을 확인하고, H1의 다른 입력 종류와 H2의 손실·발명을 구현 기준으로 재사용하지 않도록 구별한다.
5. 그 결정 이후에 구현 착수 여부를 다시 판단한다. 73.6%의 외부 진위나 editorial lead 품질 평가는 이번 단계의 선행 작업으로 확대하지 않는다.

## 12. 의도적으로 하지 않은 것

자산 통합, canonical schema 설계, prompt 수정, baseline 수정, HTML 수정, PDF 수정, validator·renderer·application 구현, 테스트 코드 작성, dependency 설치, package manager 초기화, 외부 조사, 누락 자산 추측, benchmark 재실행, 새로운 취재 분석 및 별도 agent 설계를 하지 않았다. Repository 산출물은 이 감사 보고서 한 개뿐이다.
