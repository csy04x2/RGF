
import re
from pathlib import Path

from pypdf import PdfReader


def extract_pdf(path: str | Path) -> str:
    reader = PdfReader(str(path))
    chunks = []
    nonempty = False

    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        nonempty |= bool(text)
        chunks.append(f"[SOURCE PAGE {i}]\n{text}")

    if not nonempty:
        raise ValueError(
            "PDF에서 추출 가능한 텍스트가 없습니다. "
            "스캔 PDF OCR은 v0.1에서 지원하지 않습니다."
        )

    return "\n\n".join(chunks)


def verify_pdf_excerpt(
    source_text: str,
    page_number: int | str | None,
    excerpt: str | None,
) -> str:
    """Check whether an AI excerpt exists on its claimed PDF page."""

    if not excerpt or not excerpt.strip():
        return "UNVERIFIABLE"

    if isinstance(page_number, bool):
        return "UNVERIFIABLE"

    try:
        page = int(page_number)
    except (TypeError, ValueError):
        return "UNVERIFIABLE"

    if page <= 0:
        return "UNVERIFIABLE"

    parts = re.split(
        r"(?m)^\[SOURCE PAGE (\d+)\]\s*$",
        source_text,
    )

    pages = {
        int(parts[i]): parts[i + 1]
        for i in range(1, len(parts) - 1, 2)
    }

    def normalize(text: str) -> str:
        return re.sub(r"\s+", "", text)

    target = normalize(excerpt)

    if page in pages and target in normalize(pages[page]):
        return "MATCH"

    if any(target in normalize(text) for text in pages.values()):
        return "PAGE_MISMATCH"

    return "NOT_FOUND"


def locate_pdf_excerpt_segments(
    source_text: str,
    excerpt: str | None,
    preferred_page: int | None = None,
) -> list[dict]:
    """Locate each quoted segment in the original PDF pages."""

    if not excerpt or not excerpt.strip():
        return []

    segments = [
        segment.strip()
        for segment in re.split(
            r"\.{3,}|\u2026+",
            excerpt,
        )
        if segment.strip()
    ]

    parts = re.split(
        r"(?m)^\[SOURCE PAGE (\d+)\]\s*$",
        source_text,
    )

    pages = {
        int(parts[i]): parts[i + 1]
        for i in range(1, len(parts) - 1, 2)
    }

    def normalize(text: str) -> str:
        return re.sub(r"\s+", "", text)

    results = []

    for segment in segments:
        target = normalize(segment)

        found_pages = [
            page_number
            for page_number, page_text in pages.items()
            if target in normalize(page_text)
        ]
        # A repeated exact quote is usable only when it also appears
        # on the PDF page explicitly cited by the analysis.
        if preferred_page is not None and preferred_page in found_pages:
            found_pages = [preferred_page]

        results.append({
            "excerpt": segment,
            "pages": found_pages,
            "verified": bool(found_pages),
        })

    return results


def pdf_excerpt_context(source_text: str, location_label: str, excerpt: str, radius: int = 135) -> str | None:
    """Return surrounding extracted text only if exact whitespace-insensitive quote matches its page."""
    page_match = re.fullmatch(r"PDF\s+(\d+)", location_label or "")
    if not page_match or not source_text or not excerpt or not excerpt.strip():
        return None
    page = int(page_match.group(1))
    parts = re.split(r"(?m)^\[SOURCE PAGE (\d+)\]\s*$", source_text)
    pages = {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
    body = pages.get(page)
    if not body:
        return None

    # Preserve offsets into the original PDF-extracted text while ignoring only whitespace.
    positions = [i for i, ch in enumerate(body) if not ch.isspace()]
    condensed = "".join(body[i] for i in positions)
    target = "".join(ch for ch in excerpt if not ch.isspace())
    if not target:
        return None
    match_at = condensed.find(target)
    if match_at < 0:
        return None
    start = positions[match_at]
    end = positions[match_at + len(target) - 1] + 1
    left, right = max(0, start - radius), min(len(body), end + radius)
    snippet = body[left:right].strip()
    return ("…" if left else "") + snippet + ("…" if right < len(body) else "")
