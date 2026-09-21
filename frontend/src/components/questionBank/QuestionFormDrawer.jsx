import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'

import { createLabel } from '../../api/labels'
import { createQuestion, updateQuestion } from '../../api/questions'
import { useCatalog } from '../../contexts/CatalogContext'
import { applyApiErrors, getApiErrorMessage } from '../../utils/apiErrors'
import {
  Box,
  Button,
  FormField,
  FormRootError,
  Input,
  IntegerInput,
  Offcanvas,
  Select,
  Textarea,
} from '../common_ui'

const OPTION_KEYS = ['A', 'B', 'C', 'D']

const schema = z
  .object({
    text: z.string().trim().min(1, 'Enter the question'),
    question_type: z.enum(['mcq', 'short', 'long'], {
      message: 'Select a type',
    }),
    marks: z.coerce
      .number({ message: 'Enter marks' })
      .int()
      .min(1, 'Marks must be at least 1'),
    difficulty: z.enum(['easy', 'medium', 'hard'], {
      message: 'Select a difficulty',
    }),
    grade: z.coerce.number().int().positive('Select a class'),
    subject: z.coerce.number().int().positive('Select a subject'),
    label_ids: z.array(z.number().int().positive()).default([]),
    correct_answer: z.string().optional().or(z.literal('')),
    option_A: z.string().optional().or(z.literal('')),
    option_B: z.string().optional().or(z.literal('')),
    option_C: z.string().optional().or(z.literal('')),
    option_D: z.string().optional().or(z.literal('')),
  })
  .superRefine((data, ctx) => {
    if (data.question_type !== 'mcq') return

    const filled = OPTION_KEYS.filter(
      (key) => data[`option_${key}`]?.trim(),
    )
    if (filled.length < 2) {
      ctx.addIssue({
        code: 'custom',
        message: 'Add at least two options',
        path: ['option_A'],
      })
    }

    const answer = data.correct_answer?.trim().toUpperCase()
    if (!answer || !OPTION_KEYS.includes(answer)) {
      ctx.addIssue({
        code: 'custom',
        message: 'Select the correct answer',
        path: ['correct_answer'],
      })
      return
    }

    if (!data[`option_${answer}`]?.trim()) {
      ctx.addIssue({
        code: 'custom',
        message: 'Correct answer must match a filled option',
        path: ['correct_answer'],
      })
    }
  })

const emptyDefaults = {
  text: '',
  question_type: '',
  marks: 1,
  difficulty: '',
  grade: '',
  subject: '',
  label_ids: [],
  correct_answer: '',
  option_A: '',
  option_B: '',
  option_C: '',
  option_D: '',
}

function questionToFormValues(question) {
  const options = [...(question.options || [])].sort(
    (a, b) => a.order - b.order,
  )
  const byIndex = Object.fromEntries(
    OPTION_KEYS.map((key, index) => [
      `option_${key}`,
      options[index]?.text ?? '',
    ]),
  )

  let correctAnswer = ''
  const correctIndex = options.findIndex((opt) => opt.is_correct)
  if (correctIndex >= 0 && correctIndex < OPTION_KEYS.length) {
    correctAnswer = OPTION_KEYS[correctIndex]
  } else if (question.correct_answer) {
    const raw = String(question.correct_answer).trim().toUpperCase()
    correctAnswer = OPTION_KEYS.includes(raw) ? raw : ''
  }

  return {
    text: question.text ?? '',
    question_type: question.question_type ?? '',
    marks: question.marks ?? 1,
    difficulty: question.difficulty ?? '',
    grade: question.grade ?? '',
    subject: question.subject ?? '',
    label_ids: (question.labels || []).map((label) => label.id),
    correct_answer: correctAnswer,
    ...byIndex,
  }
}

function buildPayload(values) {
  const payload = {
    text: values.text.trim(),
    question_type: values.question_type,
    marks: values.marks,
    difficulty: values.difficulty,
    grade: values.grade,
    subject: values.subject,
    label_ids: values.label_ids || [],
    correct_answer: values.correct_answer?.trim() || '',
  }

  if (values.question_type === 'mcq') {
    const options = OPTION_KEYS.map((key, index) => {
      const text = values[`option_${key}`]?.trim() || ''
      if (!text) return null
      return {
        text,
        is_correct: values.correct_answer?.toUpperCase() === key,
        order: index + 1,
      }
    }).filter(Boolean)

    payload.options = options
    payload.correct_answer = values.correct_answer?.toUpperCase() || ''
  }

  return payload
}

export default function QuestionFormDrawer({
  open,
  mode = 'create',
  question = null,
  labels = [],
  onClose,
  onSaved,
  onLabelsChange,
}) {
  const { grades, subjects } = useCatalog()
  const [newLabelName, setNewLabelName] = useState('')
  const [labelError, setLabelError] = useState(null)
  const [addingLabel, setAddingLabel] = useState(false)
  const readOnly = mode === 'view'

  const {
    register,
    control,
    handleSubmit,
    setError,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: emptyDefaults,
  })

  const questionType = useWatch({ control, name: 'question_type' })

  useEffect(() => {
    if (!open) return
    setNewLabelName('')
    setLabelError(null)
    if ((mode === 'edit' || mode === 'view') && question) {
      reset(questionToFormValues(question))
    } else {
      reset(emptyDefaults)
    }
  }, [open, mode, question, reset])

  const onSubmit = async (values) => {
    if (readOnly) return
    const payload = buildPayload(values)
    try {
      const { data } =
        mode === 'edit' && question
          ? await updateQuestion(question.id, payload)
          : await createQuestion(payload)
      onSaved?.(data)
    } catch (err) {
      applyApiErrors(err, setError)
    }
  }

  async function handleAddLabel() {
    const name = newLabelName.trim()
    if (!name) {
      setLabelError('Enter a topic name')
      return
    }

    const existing = labels.find(
      (label) => label.name.toLowerCase() === name.toLowerCase(),
    )
    if (existing) {
      setNewLabelName('')
      setLabelError(null)
      return existing
    }

    setAddingLabel(true)
    setLabelError(null)
    try {
      const { data } = await createLabel({ name })
      onLabelsChange?.(data)
      setNewLabelName('')
      return data
    } catch (err) {
      setLabelError(getApiErrorMessage(err, 'Could not create topic'))
      return null
    } finally {
      setAddingLabel(false)
    }
  }

  const title =
    mode === 'view'
      ? 'View Question'
      : mode === 'edit'
        ? 'Edit Question'
        : 'Add Question'

  return (
    <Offcanvas
      open={open}
      onClose={onClose}
      title={title}
      width="440px"
      footer={
        <>
          <Button
            type="button"
            variant="outline-secondary"
            disabled={isSubmitting}
            onClick={onClose}
          >
            {readOnly ? 'Close' : 'Cancel'}
          </Button>
          {!readOnly && (
            <Button
              type="submit"
              form="question-bank-form"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving…' : 'Save'}
            </Button>
          )}
        </>
      }
    >
      <form id="question-bank-form" onSubmit={handleSubmit(onSubmit)} noValidate>
        <fieldset disabled={readOnly} className="border-0 p-0 m-0">
        <FormField
          id="qb-text"
          label="Question"
          error={errors.text?.message}
        >
          <Textarea {...register('text')} style={{ height: '100px' }} />
        </FormField>

        <Box className="row g-3">
          <FormField
            id="qb-type"
            label="Type"
            error={errors.question_type?.message}
            className="col-sm-6"
          >
            <Select {...register('question_type')}>
              <option value="">Select type</option>
              <option value="mcq">MCQ</option>
              <option value="short">Short</option>
              <option value="long">Long</option>
            </Select>
          </FormField>

          <FormField
            id="qb-marks"
            label="Marks"
            error={errors.marks?.message}
            className="col-sm-6"
          >
            <IntegerInput min={1} {...register('marks')} />
          </FormField>
        </Box>

        <Box className="row g-3">
          <FormField
            id="qb-grade"
            label="Class"
            error={errors.grade?.message}
            className="col-sm-6"
          >
            <Select {...register('grade')}>
              <option value="">Select class</option>
              {grades.map((grade) => (
                <option key={grade.id} value={grade.id}>
                  {grade.name}
                </option>
              ))}
            </Select>
          </FormField>

          <FormField
            id="qb-subject"
            label="Subject"
            error={errors.subject?.message}
            className="col-sm-6"
          >
            <Select {...register('subject')}>
              <option value="">Select subject</option>
              {subjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </Select>
          </FormField>
        </Box>

        {questionType === 'mcq' && (
          <Box className="mb-3">
            <p className="form-label mb-2">Options</p>
            {OPTION_KEYS.map((key) => (
              <FormField
                key={key}
                id={`qb-option-${key}`}
                label={`${key}.`}
                error={key === 'A' ? errors.option_A?.message : undefined}
                className="mb-2"
              >
                <Input {...register(`option_${key}`)} />
              </FormField>
            ))}

            <FormField
              id="qb-correct"
              label="Correct Answer"
              error={errors.correct_answer?.message}
            >
              <Select {...register('correct_answer')}>
                <option value="">Select answer</option>
                {OPTION_KEYS.map((key) => (
                  <option key={key} value={key}>
                    {key}
                  </option>
                ))}
              </Select>
            </FormField>
          </Box>
        )}

        {questionType !== 'mcq' && (
          <FormField
            id="qb-answer"
            label="Model answer (optional)"
            error={errors.correct_answer?.message}
          >
            <Textarea {...register('correct_answer')} style={{ height: '80px' }} />
          </FormField>
        )}

        <Box className="mb-3">
          <p className="form-label mb-2">Topics</p>
          {errors.label_ids?.message && (
            <div className="invalid-feedback d-block mb-2">
              {errors.label_ids.message}
            </div>
          )}

          <Controller
            name="label_ids"
            control={control}
            render={({ field }) => {
              const selected = labels.filter((label) =>
                field.value.includes(label.id),
              )
              const available = labels.filter(
                (label) => !field.value.includes(label.id),
              )

              return (
                <Box>
                  {selected.length > 0 && (
                    <Box className="d-flex flex-wrap gap-2 mb-2">
                      {selected.map((label) => (
                        <span
                          key={label.id}
                          className="badge text-bg-light border d-inline-flex align-items-center gap-1"
                        >
                          {label.name}
                          {!readOnly && (
                            <button
                              type="button"
                              className="btn-close"
                              style={{ fontSize: '0.55rem' }}
                              aria-label={`Remove ${label.name}`}
                              onClick={() =>
                                field.onChange(
                                  field.value.filter((id) => id !== label.id),
                                )
                              }
                            />
                          )}
                        </span>
                      ))}
                    </Box>
                  )}

                  {!readOnly && (
                    <>
                      <Box className="d-flex gap-2 align-items-start">
                        <Select
                          className="flex-grow-1"
                          value=""
                          onChange={(e) => {
                            const id = Number(e.target.value)
                            if (!id || field.value.includes(id)) return
                            field.onChange([...field.value, id])
                          }}
                        >
                          <option value="">Add existing topic…</option>
                          {available.map((label) => (
                            <option key={label.id} value={label.id}>
                              {label.name}
                            </option>
                          ))}
                        </Select>
                      </Box>

                      <Box className="d-flex gap-2 mt-2">
                        <Input
                          placeholder="New topic"
                          value={newLabelName}
                          onChange={(e) => setNewLabelName(e.target.value)}
                          onKeyDown={async (e) => {
                            if (e.key !== 'Enter') return
                            e.preventDefault()
                            const created = await handleAddLabel()
                            if (created && !field.value.includes(created.id)) {
                              field.onChange([...field.value, created.id])
                            }
                          }}
                        />
                        <Button
                          type="button"
                          variant="outline-secondary"
                          disabled={addingLabel}
                          onClick={async () => {
                            const created = await handleAddLabel()
                            if (created && !field.value.includes(created.id)) {
                              field.onChange([...field.value, created.id])
                            }
                          }}
                        >
                          + Add
                        </Button>
                      </Box>
                      {labelError && (
                        <div className="invalid-feedback d-block">{labelError}</div>
                      )}
                    </>
                  )}
                </Box>
              )
            }}
          />
        </Box>

        <FormField
          id="qb-difficulty"
          label="Difficulty"
          error={errors.difficulty?.message}
        >
          <Select {...register('difficulty')}>
            <option value="">Select difficulty</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </Select>
        </FormField>

        <FormRootError message={errors.root?.message} />
        </fieldset>
      </form>
    </Offcanvas>
  )
}
