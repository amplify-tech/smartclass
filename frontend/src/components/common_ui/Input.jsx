import { forwardRef } from 'react'

import { cx } from './cx'

/**
 * Bootstrap form control. Forwards ref for React Hook Form.
 */
const Input = forwardRef(function Input(
  { type = 'text', invalid = false, className, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      className={cx('form-control', invalid && 'is-invalid', className)}
      {...rest}
    />
  )
})

export default Input
