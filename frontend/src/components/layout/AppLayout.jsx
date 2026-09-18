import { Outlet } from 'react-router-dom'

import { Box, Button, Navbar, Sidebar } from '../common_ui'
import { redirectToAuth } from '../../utils/authRedirect'

const SIDEBAR_ITEMS = [
  { to: '/', label: 'Home', end: true },
  { to: '/question-bank', label: 'Question Bank' },
  { to: '/exams', label: 'Exam' },
  { to: '/documents', label: 'Document' },
  { to: '/ppts', label: 'PPT' },
]

export default function AppLayout() {
  const handleLogout = () => {
    redirectToAuth()
  }

  return (
    <Box className="min-vh-100 d-flex flex-column bg-white">
      <Navbar>
        <Button
          type="button"
          variant="outline-secondary"
          size="sm"
          onClick={handleLogout}
        >
          Sign out
        </Button>
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
