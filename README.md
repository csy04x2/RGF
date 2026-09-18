# RGF — Reporting Gap Finder

RGF는 공식 문서에서 기자가 추가 취재해야 할 Reporting Gap과 Reporting Lead를 발견하고, 그 발견을 원문 근거까지 추적하며, 구체적인 취재 행동으로 연결하기 위한 AI-assisted journalism tool이다.

RGF는 다음이 아니다.

- 보도자료 요약기
- 자동 기사 작성기
- autonomous fact-checker
- 정부 발표를 그대로 재구성하는 dashboard

핵심 질문: **“이 문서에서 무엇을 더 취재하면 의미 있는 보도가 될 수 있는가?”**

Conceptual workflow:

DISCOVER → VERIFY / TRACE → FOLLOW UP

Information relationship:

SOURCE → DISCOVERY → REPORT → EVIDENCE

Standalone v0.1의 목표:

PDF → Source Structuring → Reporting Discovery → Validation → Canonical JSON → Deterministic Reporting Brief

현재 단계는 **Migration / Foundation (Foundation-01)**이다. 아직 실행 가능한 application은 없다. 실제 Opal migration assets는 이후 단계에서 제공된다.

목적과 책임 경계는 [architecture](docs/architecture.md), 취재 방법론은 [methodology](docs/methodology.md), 알려진 실패는 [known failures](docs/known-failures.md)에 보존한다.
