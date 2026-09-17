import { NavLink } from 'react-router-dom'

import Box from './Box'
import { cx } from './cx'

/**
 * Left navigation sidebar.
 * @param {{ to: string, label: string }[]} items
 */
export default function Sidebar({ items = [], className, ...rest }) {
  return (
    <Box
      as="aside"
      className={cx(
        'border-end bg-light flex-shrink-0 py-3',
        className,
      )}
      style={{ width: 220, minHeight: 'calc(100vh - 56px)' }}
      {...rest}
    >
      <Box as="nav" className="nav flex-column px-2 gap-1">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cx(
                'nav-link rounded px-3 py-2',
                isActive ? 'active bg-primary text-white' : 'text-dark',
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </Box>
    </Box>
  )
}
