import { clearTokens, isAuthenticated } from './authTokens'

export function redirectToAuth() {
  clearTokens()
  if (window.location.pathname !== '/login') {
    window.location.replace('/login')
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

    const onAuthPage = window.location.pathname === '/login'
    if (!isAuthenticated() && !onAuthPage) {
      window.location.replace('/login')
      return
    }
    if (isAuthenticated() && onAuthPage) {
      window.location.replace('/')
    }
  })
}
