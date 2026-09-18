import Box from './Box'
import { cx } from './cx'

/**
 * Right-side drawer (Bootstrap offcanvas). Controlled via `open`.
 * Backdrop click closes when `onClose` is provided.
 */
export default function Offcanvas({
  open = false,
  onClose,
  title,
  children,
  footer,
  className,
  bodyClassName,
  width = '420px',
}) {
  if (!open) return null

  return (
    <>
      <Box
        className="offcanvas-backdrop fade show"
        onClick={onClose}
        aria-hidden="true"
      />
      <Box
        as="aside"
        className={cx(
          'offcanvas offcanvas-end show d-flex flex-column',
          className,
        )}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === 'string' ? title : undefined}
        style={{ visibility: 'visible', width }}
      >
        <Box className="offcanvas-header border-bottom">
          <h2 className="offcanvas-title h5 mb-0">{title}</h2>
          {onClose && (
            <button
              type="button"
              className="btn-close"
              aria-label="Close"
              onClick={onClose}
            />
          )}
        </Box>
        <Box className={cx('offcanvas-body flex-grow-1', bodyClassName)}>
          {children}
        </Box>
        {footer && (
          <Box className="border-top p-3 d-flex justify-content-end gap-2">
            {footer}
          </Box>
        )}
      </Box>
    </>
  )
}
