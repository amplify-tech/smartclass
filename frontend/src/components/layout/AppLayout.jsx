import { Link, Outlet } from 'react-router-dom'

import { Box, Button, Navbar, Sidebar } from '../common_ui'
import { clearTokens, isAuthenticated } from '../../utils/authTokens'

const SIDEBAR_ITEMS = [
  { to: '/', label: 'Home', end: true },
  { to: '/question-bank', label: 'Question Bank' },
  { to: '/exams', label: 'Exam' },
  { to: '/documents', label: 'Document' },
  { to: '/ppts', label: 'PPT' },
]

export default function AppLayout() {
  const signedIn = isAuthenticated()

  const handleLogout = () => {
    clearTokens()
    window.location.assign('/auth')
  }

  return (
    <Box className="min-vh-100 d-flex flex-column bg-white">
      <Navbar>
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
      </Navbar>

      <Box className="d-flex flex-grow-1">
        <Sidebar items={SIDEBAR_ITEMS} />
        <Box as="main" className="flex-grow-1 p-4 overflow-auto">
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
