import CreateExamForm from '../components/exams/CreateExamForm'
import { Box, Card, CardBody, PageHeader } from '../components/common_ui'

export default function CreateExamPage() {
  return (
    <Box className="mx-auto" style={{ maxWidth: '40rem' }}>
      <PageHeader
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'Exams', to: '/exams' },
          { label: 'Create' },
        ]}
        title="Create Exam"
        description="Step 1 of 2 — set exam details, then select questions."
      />
      <Card>
        <CardBody className="sc-card-body">
          <CreateExamForm />
        </CardBody>
      </Card>
    </Box>
  )
}
