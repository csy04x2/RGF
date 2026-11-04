import pytest
from pathlib import Path
from pypdf import PdfWriter
from app.pdf import extract_pdf
def test_blank_pdf_error(tmp_path):
    p=tmp_path/'blank.pdf'; w=PdfWriter(); w.add_blank_page(width=100,height=100); w.write(p)
    with pytest.raises(ValueError,match='OCR'): extract_pdf(p)
def test_benchmark_pdf_extracts():
    p=Path('docs/legacy-opal/benchmark/deepfake-policy-source-2024-11.pdf')
    text=extract_pdf(p); assert '[SOURCE PAGE 1]' in text


from app.pdf import verify_pdf_excerpt


def test_verify_excerpt_same_page():
    source = (
        "[SOURCE PAGE 1]\n"
        "정부는 정책을 발표했다.\n\n"
        "[SOURCE PAGE 2]\n"
        "텔레그램과 핫라인 구축(9.3)\n"
        "실무 협의를 진행했다."
    )

    assert verify_pdf_excerpt(
        source,
        2,
        "텔레그램과핫라인구축(9.3)",
    ) == "MATCH"


def test_verify_excerpt_wrong_page():
    source = (
        "[SOURCE PAGE 1]\n"
        "정부는 정책을 발표했다.\n\n"
        "[SOURCE PAGE 2]\n"
        "텔레그램과 핫라인 구축(9.3)"
    )

    assert verify_pdf_excerpt(
        source,
        1,
        "텔레그램과 핫라인 구축(9.3)",
    ) == "PAGE_MISMATCH"


def test_verify_excerpt_not_found():
    source = (
        "[SOURCE PAGE 1]\n"
        "정부는 정책을 발표했다."
    )

    assert verify_pdf_excerpt(
        source,
        1,
        "정책 시행으로 범죄가 90% 감소했다.",
    ) == "NOT_FOUND"


def test_verify_excerpt_missing_information():
    source = "[SOURCE PAGE 1]\n정부는 정책을 발표했다."

    assert verify_pdf_excerpt(
        source,
        None,
        "정부는 정책을 발표했다.",
    ) == "UNVERIFIABLE"

    assert verify_pdf_excerpt(
        source,
        1,
        None,
    ) == "UNVERIFIABLE"


from app.pdf import locate_pdf_excerpt_segments


def test_locate_segments_across_pages():
    source = (
        "[SOURCE PAGE 1]\n"
        "Hotline established.\n\n"
        "[SOURCE PAGE 2]\n"
        "177 items deleted."
    )

    results = locate_pdf_excerpt_segments(
        source,
        "Hotline established...177 items deleted.",
    )

    assert len(results) == 2
    assert results[0]["pages"] == [1]
    assert results[1]["pages"] == [2]
    assert all(item["verified"] for item in results)


def test_locate_segments_with_missing_text():
    source = "[SOURCE PAGE 1]\nHotline established."

    results = locate_pdf_excerpt_segments(
        source,
        "Hotline established...Unverified claim.",
    )

    assert results[0]["verified"] is True
    assert results[1]["verified"] is False
    assert results[1]["pages"] == []


def test_locate_segments_missing_excerpt():
    assert locate_pdf_excerpt_segments(
        "[SOURCE PAGE 1]\nText",
        None,
    ) == []
