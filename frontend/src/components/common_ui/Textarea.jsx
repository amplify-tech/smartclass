import { forwardRef } from 'react'

import { cx } from './cx'

/**
 * Bootstrap long-text control. Forwards ref for React Hook Form.
 * Default height suits FormField floating labels.
 */
const Textarea = forwardRef(function Textarea(
  { invalid = false, className, style, ...rest },
  ref,
) {
  return (
    <textarea
      ref={ref}
      className={cx('form-control', invalid && 'is-invalid', className)}
      style={{ height: '120px', ...style }}
      {...rest}
    />
  )
})

export default Textarea
