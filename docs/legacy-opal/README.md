# Legacy Opal migration

Google Opal은 RGF의 prototype, reasoning laboratory, prompt development environment, failure archive였다. Opal 자체를 standalone architecture로 그대로 복제하지 않는다.

향후 이 디렉터리에 migration될 수 있는 asset:

- final source-structuring prompt
- final reporting-discovery prompt
- final validation prompt
- actual strict JSON output
- validation output
- representative Generate Brief HTML failures
- legacy notes/provenance

Foundation-01 당시에는 실제 파일이 제공되지 않았다. Foundation-02에서 자산을 migration했고, 이후 source-structuring prompt를 추가 이전했다. Asset 내용을 추측하여 재구성하지 않는다. 기존 Opal output은 GOLD ANSWER가 아닌 legacy baseline으로 취급한다.

## Migrated assets — Foundation-02

다음은 repository root 기준 상대경로다.

- benchmark source: `docs/legacy-opal/benchmark/deepfake-policy-source-2024-11.pdf`
- source-structuring prompt (추가 이전 완료): `docs/legacy-opal/prompts/source-structuring-prompt.txt`
- reporting-discovery prompt: `docs/legacy-opal/prompts/reporting-discovery-prompt.txt`
- final evidence validator prompt: `docs/legacy-opal/prompts/final-evidence-validator-prompt.txt`
- Opal reporting-analysis baseline: `docs/legacy-opal/baselines/opal-reporting-analysis-baseline.json`
- verbatim/pre-dump HTML failure: `docs/legacy-opal/failures/generate-brief-verbatim-pre-dump.html`
- pretty-but-lossy HTML failure: `docs/legacy-opal/failures/generate-brief-pretty-lossy.html`
- migration notes: `docs/legacy-opal/migration-package-notes.md`

Migration은 canonicalization이 아니다. Baseline은 gold answer가 아니다. HTML failure는 renderer template가 아니다. Source-structuring prompt는 제공된 원문으로 이전 완료했다. 독립 validation output은 여전히 미확보이며 추측 생성하지 않았다.
