import { Link } from 'react-router-dom'

import { Box, Button } from '../components/common_ui'
import { useAuth } from '../context/AuthContext'

export default function HomePage() {
  const { isAuthenticated, logout } = useAuth()

  return (
    <Box className="container py-4">
      <Box className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h3 mb-0">SmartClass</h1>
        {isAuthenticated ? (
          <Button
            type="button"
            variant="outline-secondary"
            size="sm"
            onClick={logout}
          >
            Sign out
          </Button>
        ) : (
          <Link to="/auth" className="btn btn-primary btn-sm">
            Sign in
          </Link>
        )}
      </Box>
      <p className="text-muted mb-0">AI-powered platform for teachers</p>
      {isAuthenticated && (
        <p className="mt-3 mb-0 text-success">You are signed in.</p>
      )}
    </Box>
  )
}
