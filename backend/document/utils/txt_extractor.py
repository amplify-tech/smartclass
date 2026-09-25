"""Plain-text extraction."""
from document.utils.extractors import ExtractedPage, FileExtractionError


def extract_txt(file_bytes):
    if not file_bytes:
        raise FileExtractionError('Text file is empty.')

    for encoding in ('utf-8', 'latin-1'):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = file_bytes.decode('utf-8', errors='replace')

    return [ExtractedPage(page_number=None, text=text)]
