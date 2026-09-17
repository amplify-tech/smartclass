import { Link } from 'react-router-dom'

import Box from './Box'
import { cx } from './cx'

/**
 * Top application bar. Brand links home; pass actions via children.
 */
export default function Navbar({ brand = 'SmartClass', children, className, ...rest }) {
  return (
    <Box
      as="header"
      className={cx(
        'navbar navbar-expand navbar-light bg-white border-bottom px-3',
        className,
      )}
      {...rest}
    >
      <Link to="/" className="navbar-brand mb-0 h1 fs-5">
        {brand}
      </Link>
      {children && (
        <Box className="ms-auto d-flex align-items-center gap-2">{children}</Box>
      )}
    </Box>
  )
}
