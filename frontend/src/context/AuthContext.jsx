import { createContext, useContext, useMemo, useState } from 'react'

import { clearTokens, getAccessToken, setTokens } from '../utils/authTokens'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(() => getAccessToken())

  const value = useMemo(
    () => ({
      isAuthenticated: Boolean(accessToken),
      login: (tokens) => {
        setTokens(tokens)
        setAccessToken(tokens.access)
      },
      logout: () => {
        clearTokens()
        setAccessToken(null)
      },
    }),
    [accessToken],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
