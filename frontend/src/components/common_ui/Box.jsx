import { cx } from './cx'

/**
 * Generic layout container. Prefer semantic props over raw Bootstrap class strings.
 * @param {'div'|'section'|'article'|'main'|'header'|'footer'|'form'|'span'} [as]
 */
export default function Box({
  as: Component = 'div',
  className,
  children,
  ...rest
}) {
  return (
    <Component className={cx(className)} {...rest}>
      {children}
    </Component>
  )
}
