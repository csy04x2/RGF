
from pathlib import Path

from app.pdf import extract_pdf
from app.source_repository import create_source_document


def register_pdf(file_path, title, organization=None):
    """PDF 원문을 추출하고 MySQL에 정책자료로 등록한다."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"PDF 파일을 찾을 수 없습니다: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError("PDF 파일만 등록할 수 있습니다.")

    # 1. PDF에서 원문 추출
    raw_text = extract_pdf(path)

    # 2. MySQL에 정책자료 저장
    document_id = create_source_document(
        title=title,
        source_type="PDF",
        raw_text=raw_text,
        file_path=str(path.resolve()),
        organization=organization,
    )

    # 3. 저장된 자료의 고유 ID 반환
    return document_id
