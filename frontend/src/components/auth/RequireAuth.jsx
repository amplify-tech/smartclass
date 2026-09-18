import { Outlet } from 'react-router-dom'

import { isAuthenticated } from '../../utils/authTokens'
import { redirectToAuth } from '../../utils/authRedirect'

/** Blocks app routes when no access token is stored. */
export default function RequireAuth() {
  if (!isAuthenticated()) {
    redirectToAuth()
    return null
  }

  return <Outlet />
}
