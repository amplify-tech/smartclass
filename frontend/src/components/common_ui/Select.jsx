import { forwardRef } from 'react'

import { cx } from './cx'

/**
 * Bootstrap form select. Forwards ref for React Hook Form.
 * With FormField (floating label), include an empty first option.
 */
const Select = forwardRef(function Select(
  { invalid = false, className, children, ...rest },
  ref,
) {
  return (
    <select
      ref={ref}
      className={cx('form-select', invalid && 'is-invalid', className)}
      {...rest}
    >
      {children}
    </select>
  )
})

export default Select
