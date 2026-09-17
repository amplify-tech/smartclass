import { Children, cloneElement, isValidElement } from 'react'

import { cx } from './cx'

/**
 * Floating-label field: control + label + optional error under the input.
 * Pass an Input (or similar) as the single child. Placeholder defaults to the label text.
 */
export default function FormField({
  id,
  label,
  error,
  className,
  children,
}) {
  const child = Children.only(children)
  const placeholder =
    (isValidElement(child) && child.props.placeholder) ||
    (typeof label === 'string' ? label : ' ')

  const control = isValidElement(child)
    ? cloneElement(child, {
        id: child.props.id ?? id,
        placeholder,
        invalid: child.props.invalid ?? Boolean(error),
      })
    : child

  return (
    <div className={cx('form-floating mb-3', className)}>
      {control}
      <label htmlFor={id}>{label}</label>
      {error && <div className="invalid-feedback d-block">{error}</div>}
    </div>
  )
}
