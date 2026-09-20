const STATUS_FALLBACKS = {
  400: 'Please check the highlighted fields and try again.',
  401: 'Your session has expired. Please sign in again.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested item was not found.',
  409: 'This conflicts with existing data. Refresh and try again.',
  422: 'Please check the highlighted fields and try again.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'A server error occurred. Please try again later.',
  502: 'Service temporarily unavailable. Please try again later.',
  503: 'Service temporarily unavailable. Please try again later.',
}

function firstMessage(value) {
  if (value == null) return null
  if (typeof value === 'string') return value.trim() || null
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstMessage(item)
      if (message) return message
    }
    return null
  }
  if (typeof value === 'object') {
    if (typeof value.message === 'string' && value.message.trim()) {
      return value.message.trim()
    }
    for (const nested of Object.values(value)) {
      const message = firstMessage(nested)
      if (message) return message
    }
  }
  return null
}

function extractPayloadMessage(data) {
  if (data == null) return null
  if (typeof data === 'string') return data.trim() || null
  if (typeof data !== 'object') return null

  const direct =
    firstMessage(data.error) ||
    firstMessage(data.detail) ||
    firstMessage(data.message) ||
    firstMessage(data.non_field_errors)
  if (direct) return direct

  if (data.errors && typeof data.errors === 'object') {
    const fromErrors = firstMessage(data.errors)
    if (fromErrors) return fromErrors
  }

  const reserved = new Set(['error', 'errors', 'detail', 'message'])
  for (const [key, value] of Object.entries(data)) {
    if (reserved.has(key)) continue
    const message = firstMessage(value)
    if (message) return message
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

/**
 * User-facing message for any API / network failure (lists, panels, toasts).
 */
export function getApiErrorMessage(
  error,
  fallback = 'Something went wrong. Please try again.',
) {
  const fromNetwork = networkMessage(error)
  if (fromNetwork) return fromNetwork

  const status = error?.response?.status
  const fromPayload = extractPayloadMessage(error?.response?.data)
  if (fromPayload) return fromPayload

  if (status && STATUS_FALLBACKS[status]) {
    return STATUS_FALLBACKS[status]
  }

  if (typeof error?.message === 'string' && error.message.trim()) {
    return error.message.trim()
  }

  return fallback
}

/**
 * Apply DRF / API errors onto React Hook Form.
 *
 * Supported response shapes:
 *   { "error": "message" }              → form-level (errors.root)
 *   { "errors": { "email": "…" } }      → field-level
 *   { "detail": "message" }             → form-level
 *   { "email": ["…"], … }               → field-level
 *   { "non_field_errors": ["…"] }       → form-level
 *
 * Usage:
 *   catch (err) { applyApiErrors(err, setError) }
 */
export function applyApiErrors(error, setError, fieldAliases = {}) {
  const fromNetwork = networkMessage(error)
  if (fromNetwork) {
    setError('root', { type: 'server', message: fromNetwork })
    return
  }

  const data = error?.response?.data
  const status = error?.response?.status
  const fallback = getApiErrorMessage(error)

  if (status === 401) {
    setError('root', {
      type: 'server',
      message: STATUS_FALLBACKS[401],
    })
    return
  }

  if (status === 403 || status === 404 || status === 409 || status === 429) {
    setError('root', {
      type: 'server',
      message: extractPayloadMessage(data) || STATUS_FALLBACKS[status],
    })
    if (status !== 409) return
  }

  if (status != null && status >= 500) {
    setError('root', {
      type: 'server',
      message: extractPayloadMessage(data) || STATUS_FALLBACKS[status] || fallback,
    })
    return
  }

  if (data == null) {
    setError('root', { type: 'server', message: fallback })
    return
  }

  if (typeof data === 'string') {
    setError('root', { type: 'server', message: data || fallback })
    return
  }

  if (typeof data !== 'object') {
    setError('root', { type: 'server', message: fallback })
    return
  }

  let applied = false

  if (typeof data.error === 'string' && data.error) {
    setError('root', { type: 'server', message: data.error })
    applied = true
  }

  if (typeof data.detail === 'string' && data.detail) {
    setError('root', { type: 'server', message: data.detail })
    applied = true
  }

  if (data.errors && typeof data.errors === 'object' && !Array.isArray(data.errors)) {
    applyFieldMap(data.errors, setError, fieldAliases)
    applied = true
  }

  const reserved = new Set(['error', 'errors', 'detail', 'message'])
  const topLevelFields = {}
  for (const [key, value] of Object.entries(data)) {
    if (reserved.has(key)) continue
    topLevelFields[key] = value
  }
  if (Object.keys(topLevelFields).length > 0) {
    applyFieldMap(topLevelFields, setError, fieldAliases)
    applied = true
  }

  if (!applied) {
    setError('root', { type: 'server', message: fallback })
  }
}

function applyFieldMap(map, setError, fieldAliases = {}) {
  for (const [field, messages] of Object.entries(map)) {
    const message = Array.isArray(messages)
      ? firstMessage(messages)
      : typeof messages === 'object' && messages !== null
        ? firstMessage(messages)
        : String(messages)
    if (!message) continue

    if (field === 'non_field_errors') {
      setError('root', { type: 'server', message })
      continue
    }

    const target = fieldAliases[field] || field
    setError(target, { type: 'server', message })
  }
}
