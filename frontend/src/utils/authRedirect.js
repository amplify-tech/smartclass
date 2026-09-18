import { clearTokens, isAuthenticated } from './authTokens'

export function redirectToAuth() {
  clearTokens()
  if (window.location.pathname !== '/auth') {
    window.location.replace('/auth')
  }
}

export function redirectToHome() {
  if (window.location.pathname !== '/') {
    window.location.replace('/')
  }
}

/**
 * Browser back/forward can restore pages from bfcache after logout,
 * which would otherwise show stale internal UI without remounting React.
 */
export function installAuthHistoryGuard() {
  window.addEventListener('pageshow', (event) => {
    if (!event.persisted) return

    const onAuthPage = window.location.pathname === '/auth'
    if (!isAuthenticated() && !onAuthPage) {
      window.location.replace('/auth')
      return
    }
    if (isAuthenticated() && onAuthPage) {
      window.location.replace('/')
    }
  })
}
