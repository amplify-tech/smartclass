import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listQuestionGenerationJobs } from '../api/questionGeneration'
import {
  Alert,
  Box,
  Button,
  Card,
  CardBody,
  Select,
  Spinner,
} from '../components/common_ui'
import { useCatalog } from '../contexts/CatalogContext'

const STATUS_LABELS = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
}

const STATUS_BADGE = {
  pending: 'text-bg-warning',
  running: 'text-bg-info',
  completed: 'text-bg-success',
  failed: 'text-bg-danger',
}

const DIFFICULTY_LABELS = {
  easy: 'Easy',
  medium: 'Medium',
  hard: 'Hard',
}

const TYPE_LABELS = {
  mcq: 'MCQ',
  short: 'Short',
  long: 'Long',
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString()
}

function questionTypesSummary(questionTypes) {
  if (!questionTypes || typeof questionTypes !== 'object') return '—'
  const parts = Object.entries(questionTypes)
    .filter(([, count]) => Number(count) > 0)
    .map(([type, count]) => `${TYPE_LABELS[type] || type}: ${count}`)
  return parts.length ? parts.join(', ') : '—'
}

export default function PendingTasksPage() {
  const { grades, subjects } = useCatalog()
  const [jobs, setJobs] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('active')

  const gradeLabel = useCallback(
    (id) => grades.find((g) => Number(g.id) === Number(id))?.name || '—',
    [grades],
  )

  const subjectLabel = useCallback(
    (id) => subjects.find((s) => Number(s.id) === Number(id))?.name || '—',
    [subjects],
  )

  const loadJobs = useCallback(async () => {
    setStatus('loading')
    setError(null)
    try {
      const { data } = await listQuestionGenerationJobs()
      setJobs(Array.isArray(data) ? data : data?.results || [])
      setStatus('ready')
    } catch (err) {
      setJobs([])
      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          err.message ||
          'Failed to load generation jobs',
      )
      setStatus('error')
    }
  }, [])

  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  const filteredJobs = jobs.filter((job) => {
    if (statusFilter === 'all') return true
    if (statusFilter === 'active') {
      return job.status === 'pending' || job.status === 'running'
    }
    return job.status === statusFilter
  })

  return (
    <Box>
      <Box className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <h1 className="h4 mb-0">Pending Tasks</h1>
        <Button as={Link} to="/exams/generate" variant="outline-secondary">
          + Generate Questions
        </Button>
      </Box>

      <Card>
        <CardBody className="p-4">
          <Box className="row g-2 mb-3">
            <Box className="col-6 col-md-3">
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                aria-label="Filter by status"
              >
                <option value="active">Pending / Running</option>
                <option value="all">All statuses</option>
                <option value="pending">Pending</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </Select>
            </Box>
          </Box>

          {status === 'loading' && (
            <Box className="d-flex align-items-center gap-2 py-5 justify-content-center">
              <Spinner label="Loading tasks…" />
              <span className="text-muted">Loading tasks…</span>
            </Box>
          )}

          {status === 'error' && (
            <Box className="py-3">
              <Alert variant="danger" className="mb-3">
                {error}
              </Alert>
              <Button type="button" onClick={loadJobs}>
                Try again
              </Button>
            </Box>
          )}

          {status === 'ready' && filteredJobs.length === 0 && (
            <p className="text-muted text-center py-5 mb-0">
              {jobs.length === 0
                ? 'No generation jobs yet. Start one from Generate Questions.'
                : 'No jobs match this status filter.'}
            </p>
          )}

          {status === 'ready' && filteredJobs.length > 0 && (
            <Box className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead>
                  <tr>
                    <th scope="col">Status</th>
                    <th scope="col">Class</th>
                    <th scope="col">Subject</th>
                    <th scope="col">Difficulty</th>
                    <th scope="col" className="text-end">
                      Marks
                    </th>
                    <th scope="col">Question types</th>
                    <th scope="col" className="text-end">
                      Generated
                    </th>
                    <th scope="col">Created</th>
                    <th scope="col">Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredJobs.map((job) => (
                    <tr key={job.id}>
                      <td>
                        <span
                          className={`badge ${STATUS_BADGE[job.status] || 'text-bg-secondary'}`}
                        >
                          {STATUS_LABELS[job.status] || job.status || '—'}
                        </span>
                        {job.status === 'failed' && job.error_message ? (
                          <Box
                            as="span"
                            className="d-block small text-danger mt-1"
                            title={job.error_message}
                          >
                            {job.error_message.length > 60
                              ? `${job.error_message.slice(0, 59)}…`
                              : job.error_message}
                          </Box>
                        ) : null}
                      </td>
                      <td>{gradeLabel(job.grade)}</td>
                      <td>{subjectLabel(job.subject)}</td>
                      <td>
                        {DIFFICULTY_LABELS[job.difficulty] ||
                          job.difficulty ||
                          '—'}
                      </td>
                      <td className="text-end">{job.total_marks ?? '—'}</td>
                      <td className="small">
                        {questionTypesSummary(job.question_types)}
                      </td>
                      <td className="text-end">
                        {Array.isArray(job.question_ids)
                          ? job.question_ids.length
                          : 0}
                      </td>
                      <td className="text-nowrap small text-muted">
                        {formatDate(job.created_at)}
                      </td>
                      <td className="text-nowrap small text-muted">
                        {formatDate(job.completed_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Box>
          )}
        </CardBody>
      </Card>
    </Box>
  )
}
