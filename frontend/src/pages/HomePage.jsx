import { Link } from 'react-router-dom'

import { Box, Button } from '../components/common_ui'
import { clearTokens, isAuthenticated } from '../utils/authTokens'

export default function HomePage() {
  const signedIn = isAuthenticated()

  const handleLogout = () => {
    clearTokens()
    window.location.assign('/auth')
  }

  return (
    <Box className="container py-4">
      <Box className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h3 mb-0">SmartClass</h1>
        {signedIn ? (
          <Button
            type="button"
            variant="outline-secondary"
            size="sm"
            onClick={handleLogout}
          >
            Sign out
          </Button>
        ) : (
          <Button as={Link} to="/auth" size="sm">
            Sign in
          </Button>
        )}
      </Box>
      <p className="text-muted mb-0">AI-powered platform for teachers</p>
      {signedIn && (
        <p className="mt-3 mb-0 text-success">You are signed in.</p>
      )}
    </Box>
  )
}
