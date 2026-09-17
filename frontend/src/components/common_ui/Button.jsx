import { cx } from './cx'

const VARIANTS = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  outline: 'btn-outline-primary',
  'outline-secondary': 'btn-outline-secondary',
  danger: 'btn-danger',
  link: 'btn-link',
}

/**
 * Bootstrap button wrapper.
 * @param {'primary'|'secondary'|'outline'|'outline-secondary'|'danger'|'link'} [variant]
 * @param {'sm'|'lg'} [size]
 */
export default function Button({
  type = 'button',
  variant = 'primary',
  size,
  block = false,
  className,
  disabled,
  children,
  ...rest
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={cx(
        'btn',
        VARIANTS[variant] ?? VARIANTS.primary,
        size === 'sm' && 'btn-sm',
        size === 'lg' && 'btn-lg',
        block && 'w-100',
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  )
}
