import { useId, useRef } from 'react'

import {
  formatFileSize,
  MAX_DOCUMENT_UPLOAD_BYTES,
} from '../../utils/documentLabels'
import { Box, Button, Label } from '../common_ui'
import { cx } from '../common_ui/cx'

/**
 * PDF file picker with empty and selected states (no floating label).
 */
export default function DocumentFilePicker({
  file,
  onChange,
  error,
  disabled = false,
}) {
  const inputId = useId()
  const inputRef = useRef(null)
  const maxMb = MAX_DOCUMENT_UPLOAD_BYTES / (1024 * 1024)

  const openPicker = () => {
    if (disabled) return
    inputRef.current?.click()
  }

  const handleChange = (event) => {
    const next = event.target.files?.[0] ?? null
    onChange(next)
    // Allow re-selecting the same file after Remove
    event.target.value = ''
  }

  const handleRemove = () => {
    onChange(null)
  }

  return (
    <Box className="mb-3">
      <Label htmlFor={inputId}>Document</Label>

      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept="application/pdf,.pdf"
        className="d-none"
        disabled={disabled}
        onChange={handleChange}
      />

      {file ? (
        <Box
          className={cx(
            'd-flex flex-wrap align-items-center justify-content-between gap-2 border rounded p-3',
            error && 'border-danger',
          )}
        >
          <Box className="min-w-0">
            <p className="mb-0 fw-medium text-truncate">
              <span aria-hidden="true" className="me-2">
                📄
              </span>
              {file.name}
            </p>
            <p className="mb-0 small text-muted">{formatFileSize(file.size)}</p>
          </Box>
          <Button
            type="button"
            variant="outline-secondary"
            size="sm"
            disabled={disabled}
            onClick={handleRemove}
          >
            Remove
          </Button>
        </Box>
      ) : (
        <Box
          className={cx(
            'border rounded p-4 text-center',
            error && 'border-danger',
          )}
        >
          <p className="mb-1 fw-medium">
            <span aria-hidden="true" className="me-2">
              📄
            </span>
            Choose a PDF
          </p>
          <p className="mb-3 small text-muted">PDF up to {maxMb} MB</p>
          <Button
            type="button"
            variant="outline-secondary"
            disabled={disabled}
            onClick={openPicker}
          >
            Choose File
          </Button>
        </Box>
      )}

      {error ? <div className="invalid-feedback d-block">{error}</div> : null}
    </Box>
  )
}
