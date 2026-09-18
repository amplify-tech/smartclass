import QuestionGenerationForm from '../components/exams/QuestionGenerationForm'
import { Box, Card, CardBody } from '../components/common_ui'

export default function ExamsPage() {
  return (
    <Box>
      <Card className="position-relative overflow-hidden w-100">
        <CardBody className="p-4">
          <h2 className="h5 mb-3">Generate questions</h2>
          <QuestionGenerationForm />
        </CardBody>
      </Card>
    </Box>
  )
}
