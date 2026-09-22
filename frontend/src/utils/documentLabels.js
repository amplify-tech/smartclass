/** Hardcoded document types (matches backend Document.DocType). */
export const DOC_TYPE_OPTIONS = [
  { value: 'lecture', label: 'Lecture' },
  { value: 'book', label: 'Book' },
  { value: 'dpp', label: 'DPP' },
  { value: 'previous_year', label: 'Previous Year' },
]

export const DOC_TYPE_VALUES = DOC_TYPE_OPTIONS.map((opt) => opt.value)

export const DOC_TYPE_LABELS = Object.fromEntries(
  DOC_TYPE_OPTIONS.map(({ value, label }) => [value, label]),
)

export const DOCUMENT_STATUS_LABELS = {
  uploaded: 'Uploaded',
  processing: 'Processing',
  ready: 'Ready',
  failed: 'Failed',
}

export const DOCUMENT_STATUS_TONES = {
  uploaded: 'secondary',
  processing: 'warning',
  ready: 'success',
  failed: 'danger',
}

/** Backend MAX_UPLOAD_SIZE_BYTES (10 MiB). */
export const MAX_DOCUMENT_UPLOAD_BYTES = 10 * 1024 * 1024

export function formatFileSize(bytes) {
  if (bytes == null || Number.isNaN(Number(bytes))) return '—'
  const n = Number(bytes)
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

/** Derive a document title from a PDF filename (strip extension). */
export function titleFromFilename(name) {
  const base = String(name || '').trim()
  if (!base) return 'Untitled document'
  return base.replace(/\.pdf$/i, '').trim() || 'Untitled document'
}
