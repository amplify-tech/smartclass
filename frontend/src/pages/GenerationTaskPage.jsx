import { Link, useLocation, useParams } from 'react-router-dom'

import {
  Alert,
  Box,
  Button,
  Card,
  CardBody,
  PageHeader,
  Spinner,
} from '../components/common_ui'
import { useCatalog } from '../contexts/CatalogContext'
import useQuestionGenerationJob from '../hooks/useQuestionGenerationJob'

function totalRequestedQuestions(questionTypes) {
  if (!questionTypes || typeof questionTypes !== 'object') return null
  const total = Object.values(questionTypes).reduce(
    (sum, count) => sum + (Number(count) || 0),
    0,
  )
  return total > 0 ? total : null
}

export default function GenerationTaskPage() {
  const { taskId } = useParams()
  const location = useLocation()
  const { grades, subjects } = useCatalog()
  const { job, status, error, isPolling, questionCount } =
    useQuestionGenerationJob(taskId, location.state?.job)

  const gradeName =
    grades.find((g) => Number(g.id) === Number(job?.grade))?.name ||
    (job?.grade != null ? `Class ${job.grade}` : null)

  const subjectName =
    subjects.find((s) => Number(s.id) === Number(job?.subject))?.name || null

  const description = String(job?.description || '').trim()
  const requestedCount = totalRequestedQuestions(job?.question_types)

  const metaParts = [gradeName, subjectName].filter(Boolean)
  const completedMeta = [subjectName, gradeName, description]
    .filter(Boolean)
    .join(' · ')

  const breadcrumbs = [
    { label: 'Home', to: '/' },
    { label: 'Exams', to: '/exams' },
    { label: 'Pending Tasks', to: '/exams/pending-tasks' },
    { label: taskId ? `Job #${taskId}` : 'Generation task' },
  ]

  if (!taskId) {
    return (
      <Box>
        <PageHeader breadcrumbs={breadcrumbs} title="Generation task" />
        <Alert variant="danger" className="mb-3">
          Missing generation task id.
        </Alert>
        <Button as={Link} to="/exams/pending-tasks">
          Back to Tasks
        </Button>
      </Box>
    )
  }

  if (status === 'failed' || status === 'error') {
    return (
      <Box>
        <PageHeader
          breadcrumbs={breadcrumbs}
          title="Question generation failed"
          description="We could not generate the questions this time."
        />
        <Card>
          <CardBody className="sc-card-body">
            {error ? (
              <Alert variant="danger" className="mb-4">
                {error}
              </Alert>
            ) : null}
            <Box className="d-flex flex-wrap gap-2">
              <Button as={Link} to="/exams/generate">
                Try again
              </Button>
              <Button
                as={Link}
                to="/exams/pending-tasks"
                variant="outline-secondary"
              >
                Back to Tasks
              </Button>
            </Box>
          </CardBody>
        </Card>
      </Box>
    )
  }

  if (status === 'completed') {
    return (
      <Box>
        <PageHeader
          breadcrumbs={breadcrumbs}
          title="Questions generated"
          description="Review the generated questions before using them in an exam."
        />
        <Card>
          <CardBody className="sc-card-body text-center py-5">
            <Alert variant="success" className="d-inline-block mb-3">
              Generation completed successfully
            </Alert>
            {completedMeta ? (
              <p className="text-muted mb-3">{completedMeta}</p>
            ) : null}
            <p className="mb-4 fw-semibold">
              {questionCount} question{questionCount === 1 ? '' : 's'} generated
            </p>
            <Box className="d-flex flex-wrap justify-content-center gap-2">
              <Button
                as={Link}
                to={`/exams/question-bank?jobId=${encodeURIComponent(taskId)}`}
              >
                Review Questions
              </Button>
              <Button as={Link} to="/exams/generate" variant="outline-secondary">
                Generate More
              </Button>
            </Box>
          </CardBody>
        </Card>
      </Box>
    )
  }

  const generatingLabel =
    requestedCount != null
      ? `Generating ${requestedCount} question${requestedCount === 1 ? '' : 's'}…`
      : 'Generating questions…'

  return (
    <Box>
      <PageHeader
        breadcrumbs={breadcrumbs}
        title="Generating Questions"
        description={
          metaParts.length > 0 ? metaParts.join(' · ') : undefined
        }
      />
      <Card>
        <CardBody className="sc-card-body">
          {description ? <p className="mb-4">{description}</p> : null}

          <Box
            className="d-flex flex-column align-items-center text-center py-4"
            aria-live="polite"
            aria-busy={isPolling ? 'true' : undefined}
          >
            <Spinner label={generatingLabel} className="mb-3" />
            <p className="mb-2 fw-semibold">{generatingLabel}</p>
            <p className="text-muted mb-0">
              Your questions are being prepared. This may take a few moments.
            </p>
          </Box>

          <Box className="text-center text-muted small mt-4 mb-4">
            You can leave this page. Generation continues in the background.
          </Box>

          <Box className="d-flex flex-wrap justify-content-center gap-2">
            <Button
              as={Link}
              to="/exams/pending-tasks"
              variant="outline-secondary"
            >
              View All Tasks
            </Button>
            <Button as={Link} to="/exams/generate" variant="outline-secondary">
              Generate More
            </Button>
          </Box>
        </CardBody>
      </Card>
    </Box>
  )
}
