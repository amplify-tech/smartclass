import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { listDocuments } from '../../api/documents'
import { createQuestionGenerationJob } from '../../api/questionGeneration'
import { useCatalog } from '../../contexts/CatalogContext'
import { applyApiErrors, getApiErrorMessage } from '../../utils/apiErrors'
import {
  Alert,
  Box,
  Button,
  FormField,
  FormRootError,
  IntegerInput,
  Select,
  Textarea,
} from '../common_ui'

const schema = z
  .object({
    grade: z.coerce.number().int().positive('Select a class'),
    subject: z.coerce.number().int().positive('Select a subject'),
    difficulty: z.enum(['easy', 'medium', 'hard'], {
      message: 'Select a difficulty',
    }),
    total_marks: z.coerce
      .number({ message: 'Enter total marks' })
      .int()
      .min(1, 'Total marks must be at least 1'),
    mcq: z.coerce.number().int().min(0).default(0),
    short: z.coerce.number().int().min(0).default(0),
    long: z.coerce.number().int().min(0).default(0),
    description: z.string().optional().or(z.literal('')),
    document_ids: z.array(z.number().int().positive()).default([]),
  })
  .superRefine((data, ctx) => {
    const total = data.mcq + data.short + data.long
    if (total < 1) {
      ctx.addIssue({
        code: 'custom',
        message: 'Add at least one question (MCQ, short, or long)',
        path: ['mcq'],
      })
    }
    if (total > 50) {
      ctx.addIssue({
        code: 'custom',
        message: 'Total questions cannot exceed 50',
        path: ['mcq'],
      })
    }
  })

function buildQuestionTypes({ mcq, short, long }) {
  const types = {}
  if (mcq > 0) types.mcq = mcq
  if (short > 0) types.short = short
  if (long > 0) types.long = long
  return types
}

export default function QuestionGenerationForm() {
  const navigate = useNavigate()
  const { grades, subjects } = useCatalog()
  const [documents, setDocuments] = useState([])
  const [documentsStatus, setDocumentsStatus] = useState('loading')
  const [documentsError, setDocumentsError] = useState(null)

  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      grade: '',
      subject: '',
      difficulty: '',
      total_marks: 20,
      mcq: 2,
      short: 2,
      long: 0,
      description: '',
      document_ids: [],
    },
  })

  const selectedGrade = useWatch({ control, name: 'grade' })
  const selectedSubject = useWatch({ control, name: 'subject' })

  useEffect(() => {
    let cancelled = false

    async function loadDocuments() {
      setDocumentsStatus('loading')
      setDocumentsError(null)
      try {
        const { data } = await listDocuments()
        if (cancelled) return
        setDocuments(Array.isArray(data) ? data : [])
        setDocumentsStatus('ready')
      } catch (err) {
        if (cancelled) return
        setDocuments([])
        setDocumentsError(
          getApiErrorMessage(err, 'Failed to load documents'),
        )
        setDocumentsStatus('error')
      }
    }

    loadDocuments()
    return () => {
      cancelled = true
    }
  }, [])

  const onSubmit = async (values) => {
    const payload = {
      grade: values.grade,
      subject: values.subject,
      difficulty: values.difficulty,
      total_marks: values.total_marks,
      question_types: buildQuestionTypes(values),
      description: values.description || '',
      document_ids: values.document_ids || [],
    }

    try {
      const { data } = await createQuestionGenerationJob(payload)
      navigate(`/generation-tasks/${encodeURIComponent(data.id)}`, {
        replace: true,
        state: { job: data },
      })
    } catch (err) {
      applyApiErrors(err, setError, {
        question_types: 'mcq',
      })
    }
  }

  const readyDocuments = documents.filter((doc) => {
    if (doc.status !== 'ready') return false
    if (selectedGrade && Number(doc.grade) !== Number(selectedGrade)) return false
    if (selectedSubject && Number(doc.subject) !== Number(selectedSubject)) {
      return false
    }
    return true
  })

  const isBusy = isSubmitting

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <Box className="row g-3">
        <FormField
          id="gen-grade"
          label="Class"
          error={errors.grade?.message}
          className="col-sm-6 col-lg-3"
        >
          <Select disabled={isBusy} {...register('grade')}>
            <option value="">Select class</option>
            {grades.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField
          id="gen-subject"
          label="Subject"
          error={errors.subject?.message}
          className="col-sm-6 col-lg-3"
        >
          <Select disabled={isBusy} {...register('subject')}>
            <option value="">Select subject</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField
          id="gen-difficulty"
          label="Difficulty"
          error={errors.difficulty?.message}
          className="col-sm-6 col-lg-3"
        >
          <Select disabled={isBusy} {...register('difficulty')}>
            <option value="">Select difficulty</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </Select>
        </FormField>

        <FormField
          id="gen-total-marks"
          label="Total marks"
          error={errors.total_marks?.message}
          className="col-sm-6 col-lg-3"
        >
          <IntegerInput
            min={1}
            disabled={isBusy}
            {...register('total_marks')}
          />
        </FormField>
      </Box>

      <p className="sc-section-title">Question counts</p>
      <Box className="row g-3">
        <FormField
          id="gen-mcq"
          label="MCQ"
          error={errors.mcq?.message}
          className="col-sm-4"
        >
          <IntegerInput min={0} disabled={isBusy} {...register('mcq')} />
        </FormField>
        <FormField
          id="gen-short"
          label="Short"
          error={errors.short?.message}
          className="col-sm-4"
        >
          <IntegerInput min={0} disabled={isBusy} {...register('short')} />
        </FormField>
        <FormField
          id="gen-long"
          label="Long"
          error={errors.long?.message}
          className="col-sm-4"
        >
          <IntegerInput min={0} disabled={isBusy} {...register('long')} />
        </FormField>
      </Box>

      <FormField
        id="gen-description"
        label="Description (optional)"
        error={errors.description?.message}
      >
        <Textarea disabled={isBusy} {...register('description')} />
      </FormField>

      <Box className="mb-3">
        <p className="form-label mb-2">Documents (optional)</p>
        {errors.document_ids?.message && (
          <div className="invalid-feedback d-block mb-2">
            {errors.document_ids.message}
          </div>
        )}
        {documentsStatus === 'error' && (
          <Alert variant="warning" className="mb-2 py-2">
            {documentsError} You can still generate without documents.
          </Alert>
        )}
        {!selectedGrade || !selectedSubject ? (
          <p className="text-muted small mb-0">
            Select class and subject to see ready documents.
          </p>
        ) : documentsStatus === 'loading' ? (
          <p className="text-muted small mb-0">Loading documents…</p>
        ) : readyDocuments.length === 0 ? (
          <p className="text-muted small mb-0">
            No ready documents for this class and subject.
          </p>
        ) : (
          <Controller
            name="document_ids"
            control={control}
            render={({ field }) => (
              <Box className="d-flex flex-column gap-2">
                {readyDocuments.map((doc) => {
                  const checked = field.value.includes(doc.id)
                  return (
                    <div className="form-check" key={doc.id}>
                      <input
                        className="form-check-input"
                        type="checkbox"
                        id={`doc-${doc.id}`}
                        disabled={isBusy}
                        checked={checked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            field.onChange([...field.value, doc.id])
                          } else {
                            field.onChange(
                              field.value.filter((id) => id !== doc.id),
                            )
                          }
                        }}
                      />
                      <label
                        className="form-check-label"
                        htmlFor={`doc-${doc.id}`}
                      >
                        {doc.title}
                      </label>
                    </div>
                  )
                })}
              </Box>
            )}
          />
        )}
      </Box>

      <FormRootError message={errors.root?.message} />

      <Box className="d-flex gap-2">
        <Button type="submit" disabled={isBusy}>
          {isBusy ? 'Starting…' : 'Generate questions'}
        </Button>
      </Box>
    </form>
  )
}
