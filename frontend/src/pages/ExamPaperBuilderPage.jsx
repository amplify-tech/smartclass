import { Link, useParams } from 'react-router-dom'

import ExamPaperBuilder from '../components/exams/ExamPaperBuilder'
import { Alert, Box, Button } from '../components/common_ui'

export default function ExamPaperBuilderPage() {
  const { examId } = useParams()

  if (!examId) {
    return (
      <Box>
        <Alert variant="danger" className="mb-3">
          Missing exam id.
        </Alert>
        <Button as={Link} to="/exams">
          Back to Exam List
        </Button>
      </Box>
    )
  }

  return <ExamPaperBuilder examId={examId} />
}
