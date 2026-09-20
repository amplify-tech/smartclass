import { cx } from './cx'

const VARIANTS = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  outline: 'btn-outline-primary',
  'outline-secondary': 'btn-outline-secondary',
  success: 'btn-success',
  danger: 'btn-danger',
  warning: 'btn-warning',
  link: 'btn-link',
}

/**
 * Bootstrap button wrapper. Pass `as` to render as another element (e.g. Link).
 * @param {'primary'|'secondary'|'outline'|'outline-secondary'|'success'|'danger'|'warning'|'link'} [variant]
 * @param {'sm'|'lg'} [size]
 * @param {React.ElementType} [as]
 */
export default function Button({
  as: Component = 'button',
  type = 'button',
  variant = 'primary',
  size,
  block = false,
  className,
  disabled,
  children,
  ...rest
}) {
  const props = {
    className: cx(
      'btn',
      VARIANTS[variant] ?? VARIANTS.primary,
      size === 'sm' && 'btn-sm',
      size === 'lg' && 'btn-lg',
      block && 'w-100',
      className,
    ),
    disabled,
    children,
    ...rest,
  }

  if (Component === 'button') {
    props.type = type
  }

  return <Component {...props} />
}
