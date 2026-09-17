/**
 * Map Django DRF error payloads onto React Hook Form fields.
 * Falls back to a form-level `root` message for non-field errors.
 */
export function applyApiErrors(error, setError) {
  const data = error?.response?.data

  if (!data || typeof data !== 'object') {
    setError('root', {
      type: 'server',
      message: error?.message || 'Something went wrong. Please try again.',
    })
    return
  }

  if (typeof data.detail === 'string') {
    setError('root', { type: 'server', message: data.detail })
    return
  }

  let hasFieldError = false

  for (const [field, messages] of Object.entries(data)) {
    const message = Array.isArray(messages) ? messages[0] : String(messages)

    if (field === 'non_field_errors') {
      setError('root', { type: 'server', message })
      continue
    }

    setError(field, { type: 'server', message })
    hasFieldError = true
  }

  if (!hasFieldError && !data.non_field_errors) {
    setError('root', {
      type: 'server',
      message: 'Request failed. Please check your input and try again.',
    })
  }
}
