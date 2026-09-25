"""File-type extraction strategies (.pdf, .txt)."""
from dataclasses import dataclass
from pathlib import Path


class FileExtractionError(Exception):
    """Raised when a file cannot be opened or yields no usable content."""


@dataclass(frozen=True)
class ExtractedPage:
    """One unit of extracted text (page_number is 1-based when applicable)."""

    page_number: int | None
    text: str


def _extraction_strategies():
    from document.utils.pdf_extractor import extract_pdf_pages
    from document.utils.txt_extractor import extract_txt

    return {
        '.pdf': extract_pdf_pages,
        '.txt': extract_txt,
    }


def extract_pages(file_bytes, *, filename=''):
    """Pick a file-type strategy and return ordered page text."""
    ext = Path(filename).suffix.lower()
    return _extraction_strategies()[ext](file_bytes)
