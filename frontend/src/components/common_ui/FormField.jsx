import { cx } from './cx'

import Label from './Label'

/**
 * Label + control + optional invalid-feedback group.
 * Pass the control (e.g. Input) as children.
 */
export default function FormField({
  id,
  label,
  error,
  className,
  children,
}) {
  return (
    <div className={cx('mb-3', className)}>
      {label != null && <Label htmlFor={id}>{label}</Label>}
      {children}
      {error && <div className="invalid-feedback d-block">{error}</div>}
    </div>
  )
}
