import Box from './Box'
import { cx } from './cx'

/**
 * Bootstrap spinner. Use `fullPage` for a viewport-centered loading screen.
 * @param {boolean} [fullPage]
 * @param {'sm'} [size]
 * @param {string} [label]
 */
export default function Spinner({
  fullPage = false,
  size,
  label = 'Loading…',
  className,
}) {
  const spinner = (
    <div
      className={cx(
        'spinner-border',
        size === 'sm' && 'spinner-border-sm',
        className,
      )}
      role="status"
    >
      <span className="visually-hidden">{label}</span>
    </div>
  )

  if (!fullPage) return spinner

  return (
    <Box className="min-vh-100 d-flex align-items-center justify-content-center bg-white">
      {spinner}
    </Box>
  )
}
