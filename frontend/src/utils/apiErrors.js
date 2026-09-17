/**
 * Apply DRF / API errors onto React Hook Form.
 *
 * Supported response shapes:
 *   { "error": "message" }              → form-level (errors.root), show above submit
 *   { "errors": { "email": "…" } }      → field-level, keys match input names
 *   { "detail": "message" }             → form-level (DRF default)
 *   { "email": ["…"], … }               → field-level (DRF validation)
 *   { "non_field_errors": ["…"] }       → form-level
 *
 * Usage:
 *   catch (err) { applyApiErrors(err, setError) }
 */
export function applyApiErrors(error, setError) {
  const data = error?.response?.data
  const fallback = error?.message || 'Something went wrong. Please try again.'

  if (data == null) {
    setError('root', { type: 'server', message: fallback })
    return
  }

  // Plain text body
  if (typeof data === 'string') {
    setError('root', { type: 'server', message: data || fallback })
    return
  }

  if (typeof data !== 'object') {
    setError('root', { type: 'server', message: fallback })
    return
  }

  let applied = false

  // { error: "…" } — form-level text
  if (typeof data.error === 'string' && data.error) {
    setError('root', { type: 'server', message: data.error })
    applied = true
  }

  // { detail: "…" } — DRF default form-level
  if (typeof data.detail === 'string' && data.detail) {
    setError('root', { type: 'server', message: data.detail })
    applied = true
  }

  // { errors: { field: "…" | ["…"] } } — preferred field map
  if (data.errors && typeof data.errors === 'object' && !Array.isArray(data.errors)) {
    applyFieldMap(data.errors, setError)
    applied = true
  }

  // Top-level DRF validation / non_field_errors (skip reserved keys)
  const reserved = new Set(['error', 'errors', 'detail'])
  const topLevelFields = {}
  for (const [key, value] of Object.entries(data)) {
    if (reserved.has(key)) continue
    topLevelFields[key] = value
  }
  if (Object.keys(topLevelFields).length > 0) {
    applyFieldMap(topLevelFields, setError)
    applied = true
  }

  if (!applied) {
    setError('root', { type: 'server', message: fallback })
  }
}

function applyFieldMap(map, setError) {
  for (const [field, messages] of Object.entries(map)) {
    const message = Array.isArray(messages) ? messages[0] : String(messages)
    if (!message) continue

    if (field === 'non_field_errors') {
      setError('root', { type: 'server', message })
      continue
    }

    setError(field, { type: 'server', message })
  }
}
