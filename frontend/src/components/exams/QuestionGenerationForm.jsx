import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { createQuestionGenerationJob } from '../../api/questionGeneration'
import { useCatalog } from '../../contexts/CatalogContext'
import { applyApiErrors } from '../../utils/apiErrors'
import { DOCUMENT_STATUS } from '../../utils/documentLabels'
import {
  Box,
  Button,
  FormField,
  FormRootError,
  IntegerInput,
  Select,
  Textarea,
} from '../common_ui'
import DocumentSelectModal from '../documents/DocumentSelectModal'

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
    document_ids: z.array(z.number().int().positive()).max(1).default([]),
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
  const [selectedDocument, setSelectedDocument] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)

  const {
    register,
    control,
    handleSubmit,
    setError,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      grade: grades[0]?.id ?? '',
      subject: subjects[0]?.id ?? '',
      difficulty: '',
      total_marks: 4,
      mcq: 0,
      short: 1,
      long: 0,
      description: '',
      document_ids: [],
    },
  })

  const selectedGrade = useWatch({ control, name: 'grade' })
  const selectedSubject = useWatch({ control, name: 'subject' })

  useEffect(() => {
    setSelectedDocument(null)
    setValue('document_ids', [])
    setModalOpen(false)
  }, [selectedGrade, selectedSubject, setValue])

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
      const { data: job } = await createQuestionGenerationJob(payload)
      const jobId = job?.id
      if (!jobId) {
        setError('root', {
          message: 'Could not start generation. Please try again.',
        })
        return
      }

      navigate(`/generation-tasks/${encodeURIComponent(jobId)}`, {
        replace: true,
        state: { job },
      })
    } catch (err) {
      applyApiErrors(err, setError, {
        question_types: 'mcq',
      })
    }
  }

  const isBusy = isSubmitting
  const canPickDocument = Boolean(selectedGrade && selectedSubject)

  function clearDocument() {
    setSelectedDocument(null)
    setValue('document_ids', [])
  }

  function handleDocumentSelect(doc) {
    setSelectedDocument(doc)
    setValue('document_ids', [doc.id], { shouldValidate: true })
  }

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
        <p className="form-label mb-2">Document (optional)</p>
        {errors.document_ids?.message && (
          <div className="invalid-feedback d-block mb-2">
            {errors.document_ids.message}
          </div>
        )}

        {!canPickDocument ? (
          <p className="text-muted small mb-0">
            Select class and subject to choose a document.
          </p>
        ) : selectedDocument ? (
          <Box className="d-flex flex-wrap align-items-center justify-content-between gap-2 border rounded p-3">
            <p className="mb-0 fw-medium text-truncate">
              <span aria-hidden="true" className="me-2">
                📄
              </span>
              {selectedDocument.title}
            </p>
            <Box className="d-flex gap-2">
              <Button
                type="button"
                variant="outline-secondary"
                size="sm"
                disabled={isBusy}
                onClick={() => setModalOpen(true)}
              >
                Change
              </Button>
              <Button
                type="button"
                variant="outline-secondary"
                size="sm"
                disabled={isBusy}
                onClick={clearDocument}
              >
                Remove
              </Button>
            </Box>
          </Box>
        ) : (
          <Button
            type="button"
            variant="outline-secondary"
            disabled={isBusy}
            onClick={() => setModalOpen(true)}
          >
            Select document
          </Button>
        )}
      </Box>

      <DocumentSelectModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        value={selectedDocument}
        onSelect={handleDocumentSelect}
        grade={selectedGrade}
        subject={selectedSubject}
        status={DOCUMENT_STATUS.READY}
        description="Choose a ready document to use for question generation."
      />

      <FormRootError message={errors.root?.message} />

      <Box className="d-flex gap-2">
        <Button type="submit" disabled={isBusy}>
          {isBusy ? 'Starting…' : 'Generate questions'}
        </Button>
      </Box>
    </form>
  )
}
