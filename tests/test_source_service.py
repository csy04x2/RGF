
from unittest.mock import patch

import pytest

from app.source_service import register_pdf


def test_register_pdf(tmp_path):
    """PDF 원문이 추출되어 DB 저장 함수에 전달되는지 검사한다."""

    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"test pdf")

    with (
        patch(
            "app.source_service.extract_pdf",
            return_value="[SOURCE PAGE 1]\n테스트 원문",
        ) as mock_extract,
        patch(
            "app.source_service.create_source_document",
            return_value=10,
        ) as mock_create,
    ):
        document_id = register_pdf(
            file_path=pdf_file,
            title="테스트 정책자료",
            organization="테스트 기관",
        )

    assert document_id == 10

    mock_extract.assert_called_once_with(pdf_file)

    mock_create.assert_called_once_with(
        title="테스트 정책자료",
        source_type="PDF",
        raw_text="[SOURCE PAGE 1]\n테스트 원문",
        file_path=str(pdf_file.resolve()),
        organization="테스트 기관",
    )


def test_register_pdf_missing_file(tmp_path):
    """존재하지 않는 PDF는 등록하지 않는다."""

    with pytest.raises(FileNotFoundError):
        register_pdf(
            file_path=tmp_path / "missing.pdf",
            title="테스트",
        )


def test_register_pdf_wrong_extension(tmp_path):
    """PDF가 아닌 파일은 등록하지 않는다."""

    text_file = tmp_path / "test.txt"
    text_file.write_text("테스트")

    with pytest.raises(ValueError, match="PDF"):
        register_pdf(
            file_path=text_file,
            title="테스트",
        )
