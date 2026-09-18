import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { createExam } from '../../api/exams'
import { useCatalog } from '../../contexts/CatalogContext'
import { applyApiErrors } from '../../utils/apiErrors'
import {
  Box,
  Button,
  Card,
  CardBody,
  FormField,
  FormRootError,
  Input,
  Select,
  Textarea,
} from '../common_ui'

const schema = z.object({
  title: z.string().trim().min(1, 'Enter an exam name').max(255),
  subject: z.coerce.number().int().positive('Select a subject'),
  grade: z.coerce.number().int().positive('Select a class'),
  description: z.string().optional().or(z.literal('')),
})

export default function CreateExamForm() {
  const navigate = useNavigate()
  const { grades, subjects } = useCatalog()

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      title: '',
      subject: '',
      grade: '',
      description: '',
    },
  })

  const onSubmit = async (values) => {
    const payload = {
      title: values.title.trim(),
      subject: values.subject,
      grade: values.grade,
      description: values.description?.trim() || '',
    }

    try {
      const { data } = await createExam(payload)
      navigate(
        `/exams/question-bank?mode=select&examId=${encodeURIComponent(data.id)}`,
      )
    } catch (err) {
      applyApiErrors(err, setError)
    }
  }

  return (
    <Card>
      <CardBody className="p-4">
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <FormField
            id="exam-title"
            label="Exam name"
            error={errors.title?.message}
          >
            <Input disabled={isSubmitting} {...register('title')} />
          </FormField>

          <Box className="row g-0">
            <FormField
              id="exam-subject"
              label="Subject"
              error={errors.subject?.message}
              className="col-sm-6 pe-sm-2"
            >
              <Select disabled={isSubmitting} {...register('subject')}>
                <option value=""> </option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </Select>
            </FormField>

            <FormField
              id="exam-grade"
              label="Class"
              error={errors.grade?.message}
              className="col-sm-6 ps-sm-2"
            >
              <Select disabled={isSubmitting} {...register('grade')}>
                <option value=""> </option>
                {grades.map((grade) => (
                  <option key={grade.id} value={grade.id}>
                    {grade.name}
                  </option>
                ))}
              </Select>
            </FormField>
          </Box>

          <FormField
            id="exam-instructions"
            label="Instructions (optional)"
            error={errors.description?.message}
          >
            <Textarea
              disabled={isSubmitting}
              rows={3}
              {...register('description')}
            />
          </FormField>

          <FormRootError message={errors.root?.message} />

          <Box className="d-flex justify-content-end">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating…' : 'Continue →'}
            </Button>
          </Box>
        </form>
      </CardBody>
    </Card>
  )
}
