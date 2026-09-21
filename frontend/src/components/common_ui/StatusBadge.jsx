import { cx } from './cx'

const TONE_CLASS = {
  primary: 'text-bg-primary',
  secondary: 'text-bg-secondary',
  success: 'text-bg-success',
  danger: 'text-bg-danger',
  warning: 'text-bg-warning',
  info: 'text-bg-info',
}

/**
 * @param {'primary'|'secondary'|'success'|'danger'|'warning'|'info'} [tone]
 */
export default function StatusBadge({
  tone = 'secondary',
  className,
  children,
  ...rest
}) {
  return (
    <span
      className={cx(
        'badge sc-status-badge',
        TONE_CLASS[tone] ?? TONE_CLASS.secondary,
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  )
}
