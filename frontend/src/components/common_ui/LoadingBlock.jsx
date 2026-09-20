import Box from './Box'
import Spinner from './Spinner'
import { cx } from './cx'

export default function LoadingBlock({
  label = 'Loading…',
  className,
  ...rest
}) {
  return (
    <Box
      className={cx(
        'd-flex align-items-center gap-2 py-5 justify-content-center',
        className,
      )}
      aria-live="polite"
      aria-busy="true"
      {...rest}
    >
      <Spinner label={label} />
      <span className="text-muted">{label}</span>
    </Box>
  )
}
