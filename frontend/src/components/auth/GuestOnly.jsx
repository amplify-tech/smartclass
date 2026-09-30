import { Navigate, Outlet } from 'react-router-dom'

import { isAuthenticated } from '../../utils/authTokens'

/** Auth pages only — signed-in users are sent home. */
export default function GuestOnly() {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
