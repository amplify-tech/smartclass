import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { createExam } from '../../api/exams'
import { useCatalog } from '../../contexts/CatalogContext'
import { applyApiErrors } from '../../utils/apiErrors'
import {
  Box,
  Button,
  FormField,
  FormRootError,
  Input,
  IntegerInput,
  Select,
  Textarea,
} from '../common_ui'

const schema = z.object({
  title: z.string().trim().min(1, 'Enter an exam name').max(255),
  school_name: z.string().trim().min(1, 'Enter a school name').max(255),
  subject: z.coerce.number().int().positive('Select a subject'),
  grade: z.coerce.number().int().positive('Select a class'),
  difficulty: z.union([
    z.enum(['easy', 'medium', 'hard']),
    z.literal(''),
  ]),
  duration_minutes: z.coerce
    .number()
    .int('Enter whole minutes')
    .min(1, 'Duration must be at least 1 minute')
    .max(600, 'Duration cannot exceed 600 minutes'),
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
      school_name: '',
      subject: '',
      grade: '',
      difficulty: '',
      duration_minutes: 60,
      description: '',
    },
  })

  const onSubmit = async (values) => {
    const payload = {
      title: values.title.trim(),
      school_name: values.school_name.trim(),
      subject: values.subject,
      grade: values.grade,
      duration_minutes: values.duration_minutes,
      description: values.description?.trim() || '',
    }
    if (values.difficulty) {
      payload.difficulty = values.difficulty
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
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <FormField
        id="exam-school-name"
        label="School name"
        error={errors.school_name?.message}
      >
        <Input disabled={isSubmitting} {...register('school_name')} />
      </FormField>

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
            <option value="">Select subject</option>
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
            <option value="">Select class</option>
            {grades.map((grade) => (
              <option key={grade.id} value={grade.id}>
                {grade.name}
              </option>
            ))}
          </Select>
        </FormField>
      </Box>

      <Box className="row g-0">
        <FormField
          id="exam-difficulty"
          label="Difficulty (optional)"
          error={errors.difficulty?.message}
          className="col-sm-6 pe-sm-2"
        >
          <Select disabled={isSubmitting} {...register('difficulty')}>
            <option value="">Not set</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </Select>
        </FormField>

        <FormField
          id="exam-duration"
          label="Duration (minutes)"
          error={errors.duration_minutes?.message}
          className="col-sm-6 ps-sm-2"
        >
          <IntegerInput
            disabled={isSubmitting}
            min={1}
            max={600}
            {...register('duration_minutes')}
          />
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
          placeholder={
            'Answer all questions.\nRead each question carefully.'
          }
          {...register('description')}
        />
      </FormField>

      <FormRootError message={errors.root?.message} />

      <Box className="d-flex flex-wrap justify-content-between gap-2">
        <Button
          as={Link}
          to="/exams"
          variant="outline-secondary"
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating…' : 'Continue to questions'}
        </Button>
      </Box>
    </form>
  )
}
