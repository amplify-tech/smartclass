import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listExams } from '../api/exams'
import {
  Alert,
  Box,
  Button,
  Card,
  CardBody,
  Pagination,
  Spinner,
} from '../components/common_ui'
import { useCatalog } from '../contexts/CatalogContext'
import {
  buildListParams,
  DEFAULT_PAGE_SIZE,
  parsePaginatedResponse,
} from '../utils/pagination'

const STATUS_LABELS = {
  draft: 'Draft',
  finalized: 'Finalized',
}

const DIFFICULTY_LABELS = {
  easy: 'Easy',
  medium: 'Medium',
  hard: 'Hard',
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString()
}

export default function ExamsPage() {
  const { grades, subjects } = useCatalog()
  const [exams, setExams] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(DEFAULT_PAGE_SIZE)
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(1)

  const gradeLabel = useCallback(
    (id) => grades.find((g) => Number(g.id) === Number(id))?.name || '—',
    [grades],
  )

  const subjectLabel = useCallback(
    (id) => subjects.find((s) => Number(s.id) === Number(id))?.name || '—',
    [subjects],
  )

  const loadExams = useCallback(async () => {
    setStatus('loading')
    setError(null)
    try {
      const { data } = await listExams(
        buildListParams({ page, pageSize }),
      )
      const parsed = parsePaginatedResponse(data, { page, pageSize })
      setExams(parsed.results)
      setTotalCount(parsed.count)
      setTotalPages(parsed.totalPages)
      setStatus('ready')
    } catch (err) {
      setExams([])
      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          err.message ||
          'Failed to load exams',
      )
      setStatus('error')
    }
  }, [page, pageSize])

  useEffect(() => {
    loadExams()
  }, [loadExams])

  return (
    <Box>
      <Box className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <h1 className="h4 mb-0">Exam List</h1>
        <Button as={Link} to="/exams/create">
          + Create Exam
        </Button>
      </Box>

      <Card>
        <CardBody className="p-4">
          {status === 'loading' && (
            <Box className="d-flex align-items-center gap-2 py-5 justify-content-center">
              <Spinner label="Loading exams…" />
              <span className="text-muted">Loading exams…</span>
            </Box>
          )}

          {status === 'error' && (
            <Box className="py-3">
              <Alert variant="danger" className="mb-3">
                {error}
              </Alert>
              <Button type="button" onClick={loadExams}>
                Try again
              </Button>
            </Box>
          )}

          {status === 'ready' && exams.length === 0 && (
            <p className="text-muted text-center py-5 mb-0">
              No exams yet. Create one to get started.
            </p>
          )}

          {status === 'ready' && exams.length > 0 && (
            <>
              <Box className="table-responsive">
                <table className="table table-hover align-middle mb-0">
                  <thead>
                    <tr>
                      <th scope="col">Title</th>
                      <th scope="col">Class</th>
                      <th scope="col">Subject</th>
                      <th scope="col">Difficulty</th>
                      <th scope="col" className="text-end">
                        Questions
                      </th>
                      <th scope="col" className="text-end">
                        Marks
                      </th>
                      <th scope="col">Status</th>
                      <th scope="col">Created</th>
                      <th scope="col" className="text-end">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {exams.map((exam) => (
                      <tr key={exam.id}>
                        <td className="fw-medium">{exam.title || '—'}</td>
                        <td>{gradeLabel(exam.grade)}</td>
                        <td>{subjectLabel(exam.subject)}</td>
                        <td>
                          {DIFFICULTY_LABELS[exam.difficulty] ||
                            exam.difficulty ||
                            '—'}
                        </td>
                        <td className="text-end">{exam.question_count ?? 0}</td>
                        <td className="text-end">{exam.total_marks ?? 0}</td>
                        <td>
                          <span className="badge text-bg-secondary text-capitalize">
                            {STATUS_LABELS[exam.status] || exam.status || '—'}
                          </span>
                        </td>
                        <td className="text-nowrap small text-muted">
                          {formatDate(exam.created_at)}
                        </td>
                        <td className="text-end text-nowrap">
                          <Button
                            as={Link}
                            to={`/exams/question-bank?mode=select&examId=${encodeURIComponent(exam.id)}`}
                            size="sm"
                            variant="outline-primary"
                          >
                            Add questions
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>

              <Pagination
                className="mt-3"
                page={page}
                totalPages={totalPages}
                onChange={setPage}
                count={totalCount}
                pageSize={pageSize}
              />
            </>
          )}
        </CardBody>
      </Card>
    </Box>
  )
}
