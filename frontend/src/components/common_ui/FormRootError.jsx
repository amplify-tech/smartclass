import Alert from './Alert'
import { cx } from './cx'

/**
 * Form-level API / validation message. Place directly above the submit button.
 * Pass `errors.root?.message` from React Hook Form.
 */
export default function FormRootError({ message, className, ...rest }) {
  if (!message) return null

  return (
    <Alert variant="danger" className={cx('py-2', className)} {...rest}>
      {message}
    </Alert>
  )
}
