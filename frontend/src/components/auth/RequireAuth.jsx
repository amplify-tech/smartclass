import { Navigate, Outlet } from 'react-router-dom'

import { clearTokens, isAuthenticated } from '../../utils/authTokens'

/** Blocks app routes when no access token is stored. */
export default function RequireAuth() {
  if (!isAuthenticated()) {
    clearTokens()
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
