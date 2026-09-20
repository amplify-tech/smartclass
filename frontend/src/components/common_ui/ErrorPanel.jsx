import Alert from './Alert'
import Box from './Box'
import Button from './Button'
import { cx } from './cx'

export default function ErrorPanel({
  message,
  onRetry,
  retryLabel = 'Try again',
  className,
  children,
}) {
  return (
    <Box className={cx('py-3', className)}>
      <Alert variant="danger" className="mb-3">
        {message}
      </Alert>
      <Box className="d-flex flex-wrap gap-2">
        {onRetry ? (
          <Button type="button" onClick={onRetry}>
            {retryLabel}
          </Button>
        ) : null}
        {children}
      </Box>
    </Box>
  )
}
