import { Outlet } from 'react-router-dom'

import { useCatalog } from '../../contexts/CatalogContext'
import { redirectToAuth } from '../../utils/authRedirect'
import { Box, Button, Navbar, Sidebar } from '../common_ui'

const SIDEBAR_ITEMS = [
  { to: '/', label: 'Home', end: true },
  {
    label: 'Exam',
    children: [
      { to: '/exams', label: 'Exam List', end: true },
      { to: '/exams/question-bank', label: 'Question Bank' },
      { to: '/exams/generate', label: 'Generate Questions' },
      { to: '/exams/pending-tasks', label: 'Pending Tasks' },
    ],
  },
  { to: '/documents', label: 'Document' },
  { to: '/ppts', label: 'PPT' },
]

export default function AppLayout() {
  const { user } = useCatalog()
  const displayName =
    String(user?.first_name || '').trim() || user?.email || ''

  return (
    <Box className="min-vh-100 d-flex flex-column bg-white">
      <Navbar className="d-print-none">
        {displayName ? (
          <Box as="span" className="text-secondary small">
            {displayName}
          </Box>
        ) : null}
        <Button
          type="button"
          variant="outline-secondary"
          size="sm"
          onClick={redirectToAuth}
        >
          Sign out
        </Button>
      </Navbar>

      <Box className="d-flex flex-grow-1">
        <Sidebar className="d-print-none" items={SIDEBAR_ITEMS} />
        <Box as="main" className="flex-grow-1 p-4 overflow-auto exam-print-main">
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
