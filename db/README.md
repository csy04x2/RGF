# DB 스키마와 프로젝트 구조

README §5의 MySQL 5개 테이블을 `schema.sql`로 옮겼습니다. SQL은 **아직 MySQL Server에서 실행하지 않았고**, 현재 Python CLI에도 DB 연결은 없습니다.

| 경로 | 역할 |
| --- | --- |
| `db/schema.sql` | MySQL 테이블과 외래키 정의 |
| `app/pdf.py` | PDF 텍스트 추출 |
| `app/llm.py`, `app/prompts.py` | AI 호출·프롬프트 불러오기 |
| `app/pipeline.py` | 자료 구조화→취재 분석→검증 단계 연결 |
| `app/models.py`, `schemas/` | 분석 JSON 형식 정의 |
| `app/validation.py` | 객체 참조와 결과 보존 검사 |
| `app/renderer.py`, `app/templates/` | HTML 생성 |
| `app/cli.py` | 명령줄 실행 진입점 |
| `tests/` | 자동 테스트 |
| `docs/legacy-opal/` | Opal 이전 자료 보존 |
| `requirements.txt` | Python 패키지 목록 |
| `.env.example` | 비밀값을 비운 환경변수 예시 |
| `.gitignore` | `.env` 등 로컬 파일 Git 제외 |

Workbench만으로 SQL 실행은 불가능하며 MySQL Server가 필요합니다. `source_documents.file_path` 또는 `raw_text` 중 하나가 존재해야 한다는 제약은 README 설계대로 추후 애플리케이션에서 검증합니다.
