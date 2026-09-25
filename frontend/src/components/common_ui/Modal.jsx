import { useEffect } from 'react'
import Box from './Box'
import { cx } from './cx'

const SIZE_CLASS = {
  sm: 'modal-sm',
  lg: 'modal-lg',
  xl: 'modal-xl',
  full: 'modal-fullscreen',
}

/**
 * Bootstrap modal. Controlled via `open`.
 * - `size="fit"` (default): content-sized dialog (optional `sm` / `lg` / `xl`)
 * - `size="full"`: viewport-filling dialog (works well on mobile)
 * Backdrop click and Escape close when `onClose` is provided.
 */
export default function Modal({
  open = false,
  onClose,
  title,
  children,
  footer,
  className,
  bodyClassName,
  dialogClassName,
  size = 'fit',
  centered = true,
  scrollable = true,
}) {
  useEffect(() => {
    if (!open) return undefined

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    function onKeyDown(event) {
      if (event.key === 'Escape' && onClose) onClose()
    }

    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open, onClose])

  if (!open) return null

  const sizeClass = SIZE_CLASS[size] || null
  const isFull = size === 'full'

  return (
    <>
      <Box
        className="modal-backdrop fade show"
        onClick={onClose}
        aria-hidden="true"
      />
      <Box
        className={cx('modal fade show d-block', className)}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === 'string' ? title : undefined}
        onClick={onClose}
      >
        <Box
          className={cx(
            'modal-dialog',
            !isFull && centered && 'modal-dialog-centered',
            !isFull && scrollable && 'modal-dialog-scrollable',
            sizeClass,
            // On small screens, fit modals stay usable without overflowing viewport.
            !isFull && 'mx-2 mx-sm-auto',
            dialogClassName,
          )}
          onClick={(event) => event.stopPropagation()}
        >
          <Box
            className={cx(
              'modal-content',
              isFull && 'd-flex flex-column h-100 border-0 rounded-0',
            )}
          >
            <Box className="modal-header">
              <h2 className="modal-title h5 mb-0">{title}</h2>
              {onClose && (
                <button
                  type="button"
                  className="btn-close"
                  aria-label="Close"
                  onClick={onClose}
                />
              )}
            </Box>
            <Box
              className={cx(
                'modal-body',
                isFull && 'flex-grow-1 overflow-auto',
                bodyClassName,
              )}
            >
              {children}
            </Box>
            {footer && (
              <Box className="modal-footer d-flex justify-content-end gap-2 flex-wrap">
                {footer}
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    </>
  )
}
