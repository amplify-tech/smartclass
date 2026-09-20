import Box from './Box'
import { cx } from './cx'

export default function EmptyState({
  title,
  description,
  action,
  className,
  ...rest
}) {
  return (
    <Box className={cx('sc-empty-state', className)} {...rest}>
      {title ? <p className="sc-empty-state__title">{title}</p> : null}
      {description ? (
        <p className="sc-empty-state__description">{description}</p>
      ) : null}
      {action ? <Box className="sc-empty-state__actions">{action}</Box> : null}
    </Box>
  )
}
