/**
 * DRF's default exception handler returns one of two bodies
 * (rest_framework.views.exception_handler):
 *
 *   detail is a dict  → the body is that dict
 *     { "email": ["No account found with this email."] }
 *     { "non_field_errors": ["Passwords do not match."] }
 *
 *   detail is a string → { "detail": "Wrong password." }
 */

function messageFrom(value) {
  if (typeof value === 'string') return value.trim() || null
  if (Array.isArray(value)) {
    for (const item of value) {
      if (typeof item === 'string' && item.trim()) return item.trim()
    }
  }
  return null
}

function networkMessage(error) {
  if (error?.response) return null
  if (
    error?.code === 'ERR_NETWORK' ||
    error?.message === 'Network Error' ||
    (typeof navigator !== 'undefined' && navigator.onLine === false)
  ) {
    return 'Network error. Check your connection and try again.'
  }
  return null
}

function payloadMessage(data) {
  const detail = messageFrom(data?.detail)
  if (detail) return detail

  if (data && typeof data === 'object' && !Array.isArray(data)) {
    for (const value of Object.values(data)) {
      const message = messageFrom(value)
      if (message) return message
    }
  }

  return null
}

/**
 * User-facing message for any API / network failure (lists, panels, toasts).
 */
export function getApiErrorMessage(
  error,
  fallback = 'Something went wrong. Please try again.',
) {
  return networkMessage(error) || payloadMessage(error?.response?.data) || fallback
}

/**
 * Apply a DRF error body onto React Hook Form.
 * Field dict → field errors. `{ "detail": "..." }` → form-level.
 */
export function applyApiErrors(error, setError, fieldAliases = {}) {
  const fromNetwork = networkMessage(error)
  if (fromNetwork) {
    setError('root', { type: 'server', message: fromNetwork })
    return
  }

  const data = error?.response?.data
  const detail = messageFrom(data?.detail)
  if (detail) {
    setError('root', { type: 'server', message: detail })
    return
  }

  if (data && typeof data === 'object' && !Array.isArray(data)) {
    let applied = false
    for (const [field, value] of Object.entries(data)) {
      const message = messageFrom(value)
      if (!message) continue
      applied = true
      const target =
        field === 'non_field_errors' ? 'root' : fieldAliases[field] || field
      setError(target, { type: 'server', message })
    }
    if (applied) return
  }

  setError('root', {
    type: 'server',
    message: 'Something went wrong. Please try again.',
  })
}
