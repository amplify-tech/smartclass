import { useEffect, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

import Box from './Box'
import { cx } from './cx'

/**
 * Left navigation sidebar.
 * Supports flat links and collapsible groups with `children`.
 *
 * @param {Array<{
 *   to?: string,
 *   label: string,
 *   end?: boolean,
 *   children?: Array<{ to: string, label: string, end?: boolean }>
 * }>} items
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
        {items.map((item) =>
          item.children?.length ? (
            <SidebarGroup key={item.label} item={item} />
          ) : (
            <SidebarLink key={item.to} item={item} />
          ),
        )}
      </Box>
    </Box>
  )
}

function SidebarLink({ item, className }) {
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        cx(
          'nav-link rounded px-3 py-2',
          isActive ? 'active bg-primary text-white' : 'text-dark',
          className,
        )
      }
    >
      {item.label}
    </NavLink>
  )
}

function pathMatches(pathname, to, end) {
  if (end) return pathname === to
  return pathname === to || pathname.startsWith(`${to}/`)
}

function SidebarGroup({ item }) {
  const { pathname } = useLocation()
  const childActive = item.children.some((child) =>
    pathMatches(pathname, child.to, child.end),
  )
  const [open, setOpen] = useState(childActive)

  useEffect(() => {
    if (childActive) setOpen(true)
  }, [childActive])

  return (
    <Box>
      <button
        type="button"
        className={cx(
          'nav-link rounded px-3 py-2 w-100 text-start border-0 d-flex align-items-center justify-content-between',
          childActive ? 'fw-semibold text-primary bg-transparent' : 'text-dark bg-transparent',
        )}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span>{item.label}</span>
        <span
          className="small text-muted"
          aria-hidden="true"
          style={{
            display: 'inline-block',
            transform: open ? 'rotate(90deg)' : 'none',
            transition: 'transform 0.15s ease',
          }}
        >
          ›
        </span>
      </button>

      {open ? (
        <Box className="nav flex-column gap-1 ps-2 mt-1">
          {item.children.map((child) => (
            <SidebarLink
              key={child.to}
              item={child}
              className="py-1 small"
            />
          ))}
        </Box>
      ) : null}
    </Box>
  )
}
