import { Outlet } from 'react-router-dom'

import { isAuthenticated } from '../../utils/authTokens'
import { redirectToHome } from '../../utils/authRedirect'

/** Auth pages only — signed-in users are sent home. */
export default function GuestOnly() {
  if (isAuthenticated()) {
    redirectToHome()
    return null
  }

  return <Outlet />
}
