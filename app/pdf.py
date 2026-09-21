from pathlib import Path
from pypdf import PdfReader

def extract_pdf(path:str|Path)->str:
    reader=PdfReader(str(path)); chunks=[]; nonempty=False
    for i,p in enumerate(reader.pages,1):
        text=(p.extract_text() or '').strip(); nonempty |= bool(text); chunks.append(f'[SOURCE PAGE {i}]\n{text}')
    if not nonempty: raise ValueError('PDF에서 추출 가능한 텍스트가 없습니다. 스캔 PDF OCR은 v0.1에서 지원하지 않습니다.')
    return '\n\n'.join(chunks)
