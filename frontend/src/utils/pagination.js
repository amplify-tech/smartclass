/** Default page size — keep in sync with backend StandardPagination.page_size */
export const DEFAULT_PAGE_SIZE = 20

/**
 * Normalize a DRF list response into a consistent page shape.
 * Supports both paginated `{ count, next, previous, results }` and plain arrays.
 */
export function parsePaginatedResponse(data, { page = 1, pageSize = DEFAULT_PAGE_SIZE } = {}) {
  if (Array.isArray(data)) {
    return {
      results: data,
      count: data.length,
      page,
      pageSize,
      totalPages: data.length === 0 ? 1 : 1,
      hasNext: false,
      hasPrevious: false,
    }
  }

  const results = Array.isArray(data?.results) ? data.results : []
  const count = Number(data?.count) || 0
  const totalPages = Math.max(1, Math.ceil(count / pageSize) || 1)

  return {
    results,
    count,
    page,
    pageSize,
    totalPages,
    hasNext: Boolean(data?.next),
    hasPrevious: Boolean(data?.previous),
  }
}

/**
 * Build list query params including pagination.
 * Omits empty filter values.
 */
export function buildListParams({
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE,
  ...filters
} = {}) {
  const params = {
    page,
    page_size: pageSize,
  }

  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === '') continue
    params[key] = value
  }

  return params
}
