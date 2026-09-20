import { Link, useLocation, useParams } from 'react-router-dom'

import {
  Alert,
  Box,
  Button,
  Card,
  CardBody,
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
    .join(' • ')

  if (!taskId) {
    return (
      <Box>
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
      <Card>
        <CardBody className="p-4 p-md-5">
          <h1 className="h4 mb-3">⚠ Question generation failed</h1>
          <p className="text-muted mb-2">
            We couldn&apos;t generate the questions this time.
          </p>
          {error ? (
            <Alert variant="danger" className="mb-4">
              {error}
            </Alert>
          ) : (
            <Box className="mb-4" />
          )}
          <Box className="d-flex flex-wrap gap-2">
            <Button as={Link} to="/exams/generate">
              Try Again
            </Button>
            <Button as={Link} to="/exams/pending-tasks" variant="outline-secondary">
              Back to Tasks
            </Button>
          </Box>
        </CardBody>
      </Card>
    )
  }

  if (status === 'completed') {
    return (
      <Card>
        <CardBody className="p-4 p-md-5 text-center">
          <h1 className="h4 mb-3">✓ Questions generated successfully</h1>
          {completedMeta ? (
            <p className="text-muted mb-3">{completedMeta}</p>
          ) : null}
          <p className="mb-3">
            {questionCount} question{questionCount === 1 ? '' : 's'} generated
          </p>
          <p className="text-muted mb-4">
            Review the generated questions before using them.
          </p>
          <Box className="d-flex flex-column align-items-center gap-2">
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
    )
  }

  // Loading / pending / running — clean polling state
  const generatingLabel =
    requestedCount != null
      ? `Generating ${requestedCount} question${requestedCount === 1 ? '' : 's'}…`
      : 'Generating questions…'

  return (
    <Card>
      <CardBody className="p-4 p-md-5">
        <h1 className="h4 mb-2">Generating Questions</h1>
        {metaParts.length > 0 && (
          <p className="text-muted mb-1">{metaParts.join(' • ')}</p>
        )}
        {description ? <p className="mb-4">{description}</p> : <Box className="mb-4" />}

        <Box
          className="d-flex flex-column align-items-center text-center py-4"
          aria-live="polite"
          aria-busy={isPolling ? 'true' : undefined}
        >
          <Spinner label={generatingLabel} className="mb-3" />
          <p className="mb-2 fw-semibold">{generatingLabel}</p>
          <p className="text-muted mb-0">
            Your questions are being prepared.
            <br />
            This may take a few moments.
          </p>
        </Box>

        <Box className="text-center text-muted small mt-5 mb-4">
          You can safely leave this page.
          <br />
          The generation will continue in the background.
        </Box>

        <Box className="d-flex flex-wrap justify-content-center gap-2">
          <Button as={Link} to="/exams/pending-tasks" variant="outline-secondary">
            View All Tasks
          </Button>
          <Button as={Link} to="/exams/generate" variant="outline-secondary">
            Generate More
          </Button>
        </Box>
      </CardBody>
    </Card>
  )
}
