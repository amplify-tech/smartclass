import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listExams } from '../api/exams'
import {
  Box,
  Button,
  Card,
  CardBody,
  EmptyState,
  ErrorPanel,
  LoadingBlock,
  PageHeader,
  Pagination,
  StatusBadge,
} from '../components/common_ui'
import { useCatalog } from '../contexts/CatalogContext'
import { getApiErrorMessage } from '../utils/apiErrors'
import {
  DIFFICULTY_LABELS,
  DIFFICULTY_TONE,
  EXAM_STATUS_LABELS,
  EXAM_STATUS_TONE,
} from '../utils/examLabels'
import { formatDateTime } from '../utils/formatDate'
import {
  buildListParams,
  DEFAULT_PAGE_SIZE,
  parsePaginatedResponse,
} from '../utils/pagination'

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
      const { data } = await listExams(buildListParams({ page, pageSize }))
      const parsed = parsePaginatedResponse(data, { page, pageSize })
      setExams(parsed.results)
      setTotalCount(parsed.count)
      setTotalPages(parsed.totalPages)
      setStatus('ready')
    } catch (err) {
      setExams([])
      setError(getApiErrorMessage(err, 'Failed to load exams'))
      setStatus('error')
    }
  }, [page, pageSize])

  useEffect(() => {
    loadExams()
  }, [loadExams])

  return (
    <Box>
      <PageHeader
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'Exams' },
        ]}
        title="Exam List"
        description="Create, build, and preview exam papers for your classes."
        actions={
          <Button as={Link} to="/exams/create">
            Create Exam
          </Button>
        }
      />

      <Card>
        <CardBody className="sc-card-body">
          {status === 'loading' && <LoadingBlock label="Loading exams…" />}

          {status === 'error' && (
            <ErrorPanel message={error} onRetry={loadExams} />
          )}

          {status === 'ready' && exams.length === 0 && (
            <EmptyState
              title="No exams yet"
              description="Create an exam to start selecting questions and building a paper."
              action={
                <Button as={Link} to="/exams/create">
                  Create Exam
                </Button>
              }
            />
          )}

          {status === 'ready' && exams.length > 0 && (
            <>
              <Box className="table-responsive">
                <table className="table table-hover align-middle mb-0 sc-table">
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
                    {exams.map((exam) => {
                      const difficulty = exam.difficulty
                      const examStatus = exam.status
                      return (
                        <tr key={exam.id}>
                          <td className="fw-medium">{exam.title || '—'}</td>
                          <td>{gradeLabel(exam.grade)}</td>
                          <td>{subjectLabel(exam.subject)}</td>
                          <td>
                            {difficulty ? (
                              <StatusBadge
                                tone={DIFFICULTY_TONE[difficulty] || 'secondary'}
                              >
                                {DIFFICULTY_LABELS[difficulty] || difficulty}
                              </StatusBadge>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td className="text-end">
                            {exam.question_count ?? 0}
                          </td>
                          <td className="text-end">{exam.total_marks ?? 0}</td>
                          <td>
                            <StatusBadge
                              tone={EXAM_STATUS_TONE[examStatus] || 'secondary'}
                            >
                              {EXAM_STATUS_LABELS[examStatus] ||
                                examStatus ||
                                '—'}
                            </StatusBadge>
                          </td>
                          <td className="text-nowrap small text-muted">
                            {formatDateTime(exam.created_at)}
                          </td>
                          <td className="text-end text-nowrap">
                            <Box className="d-inline-flex flex-wrap gap-2 justify-content-end">
                              <Button
                                as={Link}
                                to={`/exams/${encodeURIComponent(exam.id)}/build`}
                                size="sm"
                                variant="outline"
                              >
                                Build
                              </Button>
                              <Button
                                as={Link}
                                to={`/exams/${encodeURIComponent(exam.id)}/preview`}
                                size="sm"
                                variant="outline-secondary"
                              >
                                Preview
                              </Button>
                              <Button
                                as={Link}
                                to={`/exams/question-bank?mode=select&examId=${encodeURIComponent(exam.id)}`}
                                size="sm"
                                variant="outline-secondary"
                              >
                                Add questions
                              </Button>
                            </Box>
                          </td>
                        </tr>
                      )
                    })}
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
