import { Link } from 'react-router-dom'

import { cx } from './cx'

/**
 * @param {{ label: string, to?: string }[]} items
 */
export default function Breadcrumb({ items = [], className, ...rest }) {
  if (!items.length) return null

  return (
    <nav aria-label="Breadcrumb" className={cx(className)} {...rest}>
      <ol className="breadcrumb mb-0">
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          return (
            <li
              key={`${item.label}-${index}`}
              className={cx('breadcrumb-item', isLast && 'active')}
              aria-current={isLast ? 'page' : undefined}
            >
              {!isLast && item.to ? (
                <Link to={item.to}>{item.label}</Link>
              ) : (
                item.label
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
