# Foundation-02 — Legacy Opal Asset Migration

## Migration 목적

Google Opal에서 실제 사용·생성된 RGF 자산을 standalone 구현 전의 legacy evidence로 보존한다.

## 포함 자산

다음은 repository root 기준 상대경로다. 여섯 자산은 package 원본과 byte-for-byte 동일하게 보존했다.

- benchmark 원문 PDF: `docs/legacy-opal/benchmark/deepfake-policy-source-2024-11.pdf`
- reporting-discovery prompt: `docs/legacy-opal/prompts/reporting-discovery-prompt.txt`
- final evidence validator prompt: `docs/legacy-opal/prompts/final-evidence-validator-prompt.txt`
- 실제 Opal reporting-analysis JSON baseline: `docs/legacy-opal/baselines/opal-reporting-analysis-baseline.json`
- Generate Brief verbatim/pre-dump HTML failure: `docs/legacy-opal/failures/generate-brief-verbatim-pre-dump.html`
- Generate Brief pretty-but-lossy HTML failure: `docs/legacy-opal/failures/generate-brief-pretty-lossy.html`

## 해석 원칙

- 원문 PDF가 source authority다.
- Opal JSON은 legacy baseline이며 GOLD ANSWER가 아니다.
- prompt는 실제 Opal prompt의 보존본이며, 아직 standalone canonical prompt로 확정된 것이 아니다.
- HTML은 renderer 구현 예제가 아니라 regression failure archive다.
- pretty HTML은 object 누락·축약·재해석 가능성을 관찰하기 위한 사례다.
- `<pre>` 중심 HTML은 내용 보존과 deterministic structured rendering이 서로 다른 문제임을 보여주는 사례다.

## 확인된 중복

사용자가 제공한 migration 지시와 package notes에 따르면, 원래 제공된 `Pasted text (2).txt`와 `Pasted text (3).txt`는 SHA-256이 동일한 완전 중복 파일이었다. Repository에는 validator prompt 한 개만 보존한다.

중복 파일의 SHA-256:

`0c63b8f24cc49bc2f4a50083af77f2100632e05a48905caa267084f3a9259627`

이번 package에 포함된 validator prompt도 위 hash와 일치함을 확인했다. 원래 중복 파일 두 개는 package에 포함되지 않았다.

## 현재 누락 자산

- source-structuring prompt
- 별도의 독립 validation output

이번 migration에서는 위 자산을 추측하거나 재구성하지 않았다.

## 다음 단계와의 경계

이번 migration은 자산 보존까지만 완료한다.

아직 수행하지 않은 작업:

- canonical schema 설계
- prompt canonicalization
- deterministic validator 구현
- deterministic renderer 구현
- executable regression fixture 설계
- legacy baseline 평가
- benchmark 실행
