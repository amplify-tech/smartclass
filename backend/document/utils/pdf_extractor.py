"""PDF page text extraction (PyMuPDF)."""
import pymupdf

from document.utils.extractors import ExtractedPage, FileExtractionError


def extract_pdf_pages(file_bytes):
    if not file_bytes:
        raise FileExtractionError('PDF file is empty.')

    try:
        doc = pymupdf.open(stream=file_bytes, filetype='pdf')
    except Exception as exc:
        raise FileExtractionError(f'Invalid or unreadable PDF: {exc}') from exc

    try:
        if doc.is_encrypted and not doc.authenticate(''):
            raise FileExtractionError(
                'Encrypted PDF requires a password and cannot be processed.',
            )
        if doc.page_count == 0:
            raise FileExtractionError('PDF has no pages.')

        return [
            ExtractedPage(
                page_number=index + 1,
                text=doc.load_page(index).get_text('text') or '',
            )
            for index in range(doc.page_count)
        ]
    except FileExtractionError:
        raise
    except Exception as exc:
        raise FileExtractionError(f'Failed to extract PDF text: {exc}') from exc
    finally:
        doc.close()
