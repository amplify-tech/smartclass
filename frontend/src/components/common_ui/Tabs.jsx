import { cx } from './cx'

/**
 * Bootstrap nav-tabs list. Children should be Tab items.
 */
export function Tabs({ className, children, ...rest }) {
  return (
    <ul className={cx('nav', 'nav-tabs', className)} role="tablist" {...rest}>
      {children}
    </ul>
  )
}

/**
 * Single tab trigger. Uses Bootstrap's data-bs attributes for pane switching.
 * @param {string} target - CSS selector for the pane (e.g. "#login-pane")
 */
export function Tab({
  id,
  target,
  active = false,
  className,
  children,
  ...rest
}) {
  const paneId = target?.startsWith('#') ? target.slice(1) : target

  return (
    <li className="nav-item" role="presentation">
      <button
        type="button"
        className={cx('nav-link', active && 'active', className)}
        id={id}
        data-bs-toggle="tab"
        data-bs-target={target}
        role="tab"
        aria-controls={paneId}
        aria-selected={active}
        {...rest}
      >
        {children}
      </button>
    </li>
  )
}

/** Bootstrap tab-content wrapper. */
export function TabContent({ className, children, ...rest }) {
  return (
    <div className={cx('tab-content', className)} {...rest}>
      {children}
    </div>
  )
}

/**
 * Bootstrap tab pane.
 * @param {string} labelledBy - id of the Tab button that labels this pane
 */
export function TabPane({
  id,
  labelledBy,
  active = false,
  className,
  children,
  ...rest
}) {
  return (
    <div
      className={cx(
        'tab-pane',
        'fade',
        active && 'show active',
        className,
      )}
      id={id}
      role="tabpanel"
      aria-labelledby={labelledBy}
      tabIndex={0}
      {...rest}
    >
      {children}
    </div>
  )
}
