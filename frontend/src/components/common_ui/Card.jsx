import { cx } from './cx'

/**
 * Bootstrap card. Pair with CardBody for padded content.
 */
export function Card({ className, children, ...rest }) {
  return (
    <div className={cx('card', className)} {...rest}>
      {children}
    </div>
  )
}

/** Bootstrap card-body. */
export function CardBody({ className, children, ...rest }) {
  return (
    <div className={cx('card-body', className)} {...rest}>
      {children}
    </div>
  )
}

export default Card
