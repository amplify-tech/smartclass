import QuestionGenerationForm from '../components/exams/QuestionGenerationForm'
import { Box, Card, CardBody } from '../components/common_ui'

export default function GenerateQuestionsPage() {
  return (
    <Box>
      <h1 className="h4 mb-4">Generate Questions</h1>

      <Card className="position-relative overflow-hidden w-100">
        <CardBody className="p-4">
          <QuestionGenerationForm />
        </CardBody>
      </Card>
    </Box>
  )
}
