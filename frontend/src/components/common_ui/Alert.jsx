import { cx } from './cx'

const VARIANTS = {
  danger: 'alert-danger',
  success: 'alert-success',
  warning: 'alert-warning',
  info: 'alert-info',
  secondary: 'alert-secondary',
}

/**
 * Bootstrap alert.
 * @param {'danger'|'success'|'warning'|'info'|'secondary'} [variant]
 */
export default function Alert({
  variant = 'danger',
  className,
  children,
  ...rest
}) {
  return (
    <div
      role="alert"
      className={cx('alert', VARIANTS[variant] ?? VARIANTS.danger, className)}
      {...rest}
    >
      {children}
    </div>
  )
}
