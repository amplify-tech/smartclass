import CreateExamForm from '../components/exams/CreateExamForm'
import { Box } from '../components/common_ui'

export default function CreateExamPage() {
  return (
    <Box className="mx-auto" style={{ maxWidth: '40rem' }}>
      <h1 className="h4 mb-1">Create Exam</h1>
      <p className="text-muted small mb-4">Step 1 of 2</p>
      <CreateExamForm />
    </Box>
  )
}
