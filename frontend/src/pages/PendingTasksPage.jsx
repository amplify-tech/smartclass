import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { listQuestionGenerationJobs } from '../api/questionGeneration'
import {
  Box,
  Button,
  Card,
  CardBody,
  EmptyState,
  ErrorPanel,
  LoadingBlock,
  PageHeader,
  Select,
  StatusBadge,
} from '../components/common_ui'
import { useCatalog } from '../contexts/CatalogContext'
import { getApiErrorMessage } from '../utils/apiErrors'
import {
  DIFFICULTY_LABELS,
  JOB_STATUS_LABELS,
  JOB_STATUS_TONE,
  QUESTION_TYPE_LABELS,
} from '../utils/examLabels'
import { formatDateTime } from '../utils/formatDate'

function questionTypesSummary(questionTypes) {
  if (!questionTypes || typeof questionTypes !== 'object') return '—'
  const parts = Object.entries(questionTypes)
    .filter(([, count]) => Number(count) > 0)
    .map(([type, count]) => `${QUESTION_TYPE_LABELS[type] || type}: ${count}`)
  return parts.length ? parts.join(', ') : '—'
}

function jobStatusPath(job) {
  const id = encodeURIComponent(job.id)
  if (job.status === 'completed') {
    return `/exams/question-bank?jobId=${id}`
  }
  return `/generation-tasks/${id}`
}

export default function PendingTasksPage() {
  const navigate = useNavigate()
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
      setError(getApiErrorMessage(err, 'Failed to load generation jobs'))
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
      <PageHeader
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'Exams', to: '/exams' },
          { label: 'Pending Tasks' },
        ]}
        title="Pending Tasks"
        description="Track question generation jobs and open results when they finish."
        actions={
          <Box className="d-flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline-secondary"
              onClick={loadJobs}
              disabled={status === 'loading'}
            >
              Refresh
            </Button>
            <Button as={Link} to="/exams/generate">
              Generate Questions
            </Button>
          </Box>
        }
      />

      <Card>
        <CardBody className="sc-card-body">
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

          {status === 'loading' && <LoadingBlock label="Loading tasks…" />}

          {status === 'error' && (
            <ErrorPanel message={error} onRetry={loadJobs} />
          )}

          {status === 'ready' && filteredJobs.length === 0 && (
            <EmptyState
              title={
                jobs.length === 0
                  ? 'No generation jobs yet'
                  : 'No jobs match this filter'
              }
              description={
                jobs.length === 0
                  ? 'Start a job from Generate Questions to create bank items automatically.'
                  : 'Try another status filter or refresh the list.'
              }
              action={
                jobs.length === 0 ? (
                  <Button as={Link} to="/exams/generate">
                    Generate Questions
                  </Button>
                ) : null
              }
            />
          )}

          {status === 'ready' && filteredJobs.length > 0 && (
            <Box className="table-responsive">
              <table className="table table-hover align-middle mb-0 sc-table">
                <thead>
                  <tr>
                    <th scope="col">Job</th>
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
                    <tr
                      key={job.id}
                      role="link"
                      tabIndex={0}
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(jobStatusPath(job))}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          navigate(jobStatusPath(job))
                        }
                      }}
                    >
                      <td>
                        <Link
                          to={jobStatusPath(job)}
                          className="link-dark text-decoration-none fw-semibold"
                          onClick={(e) => e.stopPropagation()}
                        >
                          #{job.id}
                        </Link>
                      </td>
                      <td>
                        <StatusBadge
                          tone={JOB_STATUS_TONE[job.status] || 'secondary'}
                        >
                          {JOB_STATUS_LABELS[job.status] || job.status || '—'}
                        </StatusBadge>
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
                        {formatDateTime(job.created_at)}
                      </td>
                      <td className="text-nowrap small text-muted">
                        {formatDateTime(job.completed_at)}
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
