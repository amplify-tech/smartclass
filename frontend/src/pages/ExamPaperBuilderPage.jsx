import { Link, useParams } from 'react-router-dom'

import ExamPaperBuilder from '../components/exams/ExamPaperBuilder'
import { Alert, Box, Button, PageHeader } from '../components/common_ui'

export default function ExamPaperBuilderPage() {
  const { examId } = useParams()

  if (!examId) {
    return (
      <Box>
        <PageHeader
          breadcrumbs={[
            { label: 'Home', to: '/' },
            { label: 'Exams', to: '/exams' },
            { label: 'Build paper' },
          ]}
          title="Build Exam Paper"
        />
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
