import { forwardRef } from 'react'

import { cx } from './cx'

/**
 * Integer number input (Bootstrap form control). Forwards ref for React Hook Form.
 */
const IntegerInput = forwardRef(function IntegerInput(
  { invalid = false, className, ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      type="number"
      inputMode="numeric"
      step={1}
      className={cx('form-control', invalid && 'is-invalid', className)}
      {...rest}
    />
  )
})

export default IntegerInput
