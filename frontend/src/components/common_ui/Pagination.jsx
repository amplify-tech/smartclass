import Box from './Box'
import { cx } from './cx'

/**
 * Bootstrap page-number pagination.
 *
 * @param {number} page — current 1-based page
 * @param {number} totalPages
 * @param {(page: number) => void} onChange
 * @param {number} [count] — optional total result count shown as "Showing…"
 * @param {number} [pageSize]
 */
export default function Pagination({
  page,
  totalPages,
  onChange,
  count,
  pageSize,
  className,
}) {
  if (!totalPages || totalPages <= 1) {
    if (count == null) return null
    return (
      <Box
        className={cx(
          'd-flex justify-content-between align-items-center flex-wrap gap-2',
          className,
        )}
      >
        <span className="text-muted small mb-0">
          {count} result{count === 1 ? '' : 's'}
        </span>
      </Box>
    )
  }

  const pages = visiblePages(page, totalPages)
  const from = count != null && pageSize ? (page - 1) * pageSize + 1 : null
  const to =
    count != null && pageSize ? Math.min(page * pageSize, count) : null

  return (
    <Box
      className={cx(
        'd-flex justify-content-between align-items-center flex-wrap gap-2',
        className,
      )}
    >
      <span className="text-muted small mb-0">
        {from != null && to != null && count != null
          ? `Showing ${from}–${to} of ${count}`
          : null}
      </span>

      <nav aria-label="Pagination">
        <ul className="pagination pagination-sm mb-0">
          <li className={cx('page-item', page <= 1 && 'disabled')}>
            <button
              type="button"
              className="page-link"
              disabled={page <= 1}
              onClick={() => onChange(page - 1)}
              aria-label="Previous page"
            >
              Previous
            </button>
          </li>

          {pages.map((item, index) =>
            item === '…' ? (
              <li key={`ellipsis-${index}`} className="page-item disabled">
                <span className="page-link">…</span>
              </li>
            ) : (
              <li
                key={item}
                className={cx('page-item', item === page && 'active')}
              >
                <button
                  type="button"
                  className="page-link"
                  onClick={() => onChange(item)}
                  aria-label={`Page ${item}`}
                  aria-current={item === page ? 'page' : undefined}
                >
                  {item}
                </button>
              </li>
            ),
          )}

          <li className={cx('page-item', page >= totalPages && 'disabled')}>
            <button
              type="button"
              className="page-link"
              disabled={page >= totalPages}
              onClick={() => onChange(page + 1)}
              aria-label="Next page"
            >
              Next
            </button>
          </li>
        </ul>
      </nav>
    </Box>
  )
}

/** Compact page list with ellipses, e.g. 1 … 4 5 6 … 12 */
function visiblePages(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const pages = new Set([1, total, current, current - 1, current + 1])
  if (current <= 3) {
    pages.add(2)
    pages.add(3)
    pages.add(4)
  }
  if (current >= total - 2) {
    pages.add(total - 1)
    pages.add(total - 2)
    pages.add(total - 3)
  }

  const sorted = [...pages].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b)
  const result = []
  let prev = 0
  for (const n of sorted) {
    if (prev && n - prev > 1) result.push('…')
    result.push(n)
    prev = n
  }
  return result
}
