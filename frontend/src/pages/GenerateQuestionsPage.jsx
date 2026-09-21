import QuestionGenerationForm from '../components/exams/QuestionGenerationForm'
import { Box, Card, CardBody, PageHeader } from '../components/common_ui'

export default function GenerateQuestionsPage() {
  return (
    <Box>
      <PageHeader
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'Exams', to: '/exams' },
          { label: 'Generate Questions' },
        ]}
        title="Generate Questions"
        description="Create AI-assisted questions for a class and subject. Progress appears under Pending Tasks."
      />

      <Card>
        <CardBody className="sc-card-body">
          <QuestionGenerationForm />
        </CardBody>
      </Card>
    </Box>
  )
}
