import { cx } from './cx'

/** Bootstrap form label. */
export default function Label({ htmlFor, className, children, ...rest }) {
  return (
    <label htmlFor={htmlFor} className={cx('form-label', className)} {...rest}>
      {children}
    </label>
  )
}
