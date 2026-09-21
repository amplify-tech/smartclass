import Box from './Box'
import Breadcrumb from './Breadcrumb'
import { cx } from './cx'

/**
 * Consistent page chrome: breadcrumbs, title, description, actions.
 */
export default function PageHeader({
  breadcrumbs,
  title,
  description,
  actions,
  className,
  children,
}) {
  return (
    <Box className={cx('sc-page-header', className)}>
      {breadcrumbs?.length ? (
        <Breadcrumb items={breadcrumbs} className="mb-2" />
      ) : null}

      <Box className="d-flex flex-wrap align-items-start justify-content-between gap-3">
        <Box className="min-w-0">
          {title ? <h1 className="sc-page-title">{title}</h1> : null}
          {description ? (
            <p className="sc-page-description">{description}</p>
          ) : null}
          {children}
        </Box>
        {actions ? (
          <Box className="d-flex flex-wrap gap-2 flex-shrink-0">{actions}</Box>
        ) : null}
      </Box>
    </Box>
  )
}
