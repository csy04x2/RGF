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
