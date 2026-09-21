import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ReactSortable } from 'react-sortablejs'

import {
  getExam,
  removeExamQuestion,
  reorderExamQuestions,
} from '../../api/exams'
import { useCatalog } from '../../contexts/CatalogContext'
import { getApiErrorMessage } from '../../utils/apiErrors'
import { QUESTION_TYPE_LABELS } from '../../utils/examLabels'
import {
  Alert,
  Box,
  Button,
  Card,
  CardBody,
  EmptyState,
  ErrorPanel,
  LoadingBlock,
  PageHeader,
} from '../common_ui'

function labelsText(labels) {
  if (!labels?.length) return null
  return labels.map((label) => label.name).join(', ')
}

function sortPlacements(placements) {
  return [...placements].sort((a, b) => a.order - b.order)
}

function applyExamState(exam, setExam, setPlacements, setRemovedIds) {
  setExam(exam)
  setPlacements(sortPlacements(exam.exam_questions || []))
  setRemovedIds(new Set())
}

export default function ExamPaperBuilder({ examId }) {
  const navigate = useNavigate()
  const { grades, subjects } = useCatalog()

  const [exam, setExam] = useState(null)
  const [placements, setPlacements] = useState([])
  const [removedIds, setRemovedIds] = useState(() => new Set())
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [saveStatus, setSaveStatus] = useState('idle')
  const [saveError, setSaveError] = useState(null)

  const gradeName = useMemo(() => {
    if (!exam) return ''
    const match = grades.find((g) => Number(g.id) === Number(exam.grade))
    return match?.name || `Class ${exam.grade}`
  }, [exam, grades])

  const subjectName = useMemo(() => {
    if (!exam) return ''
    const match = subjects.find((s) => Number(s.id) === Number(exam.subject))
    return match?.name || ''
  }, [exam, subjects])

  const isDirty = useMemo(() => {
    if (removedIds.size > 0) return true
    return placements.some((placement, index) => placement.order !== index + 1)
  }, [placements, removedIds])

  const questionCount = placements.length
  const totalMarks = useMemo(
    () =>
      placements.reduce(
        (sum, placement) => sum + (Number(placement.question?.marks) || 0),
        0,
      ),
    [placements],
  )

  const loadExam = useCallback(async () => {
    setStatus('loading')
    setError(null)
    setSaveError(null)
    setSaveStatus('idle')
    try {
      const { data } = await getExam(examId)
      applyExamState(data, setExam, setPlacements, setRemovedIds)
      setStatus('ready')
    } catch (err) {
      setExam(null)
      setPlacements([])
      setRemovedIds(new Set())
      setError(getApiErrorMessage(err, 'Failed to load exam'))
      setStatus('error')
    }
  }, [examId])

  useEffect(() => {
    loadExam()
  }, [loadExam])

  useEffect(() => {
    if (!isDirty) return undefined
    const onBeforeUnload = (event) => {
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [isDirty])

  function removePlacement(examQuestionId) {
    setPlacements((prev) => prev.filter((item) => item.id !== examQuestionId))
    setRemovedIds((prev) => {
      const next = new Set(prev)
      next.add(examQuestionId)
      return next
    })
    setSaveError(null)
    setSaveStatus('idle')
  }

  async function handleSave() {
    if (!isDirty || saveStatus === 'saving') return

    setSaveStatus('saving')
    setSaveError(null)

    try {
      const idsToRemove = [...removedIds]
      for (const examQuestionId of idsToRemove) {
        await removeExamQuestion(examId, examQuestionId)
        setRemovedIds((prev) => {
          const next = new Set(prev)
          next.delete(examQuestionId)
          return next
        })
      }

      let data
      if (placements.length > 0) {
        const response = await reorderExamQuestions(examId, {
          items: placements.map((placement, index) => ({
            exam_question_id: placement.id,
            order: index + 1,
          })),
        })
        data = response.data
      } else {
        const response = await getExam(examId)
        data = response.data
      }

      applyExamState(data, setExam, setPlacements, setRemovedIds)
      setSaveStatus('saved')
    } catch (err) {
      setSaveStatus('error')
      setSaveError(getApiErrorMessage(err, 'Failed to save changes'))
    }
  }

  function handlePreview() {
    navigate(`/exams/${encodeURIComponent(examId)}/preview`)
  }

  const selectQuestionsPath = `/exams/question-bank?mode=select&examId=${encodeURIComponent(examId)}`

  const breadcrumbs = [
    { label: 'Home', to: '/' },
    { label: 'Exams', to: '/exams' },
    { label: exam?.title || 'Build paper' },
  ]

  if (status === 'loading') {
    return (
      <Box>
        <PageHeader
          breadcrumbs={[
            { label: 'Home', to: '/' },
            { label: 'Exams', to: '/exams' },
            { label: 'Build paper' },
          ]}
          title="Build Exam Paper"
        />
        <LoadingBlock label="Loading exam paper…" />
      </Box>
    )
  }

  if (status === 'error') {
    return (
      <Box>
        <PageHeader
          breadcrumbs={[
            { label: 'Home', to: '/' },
            { label: 'Exams', to: '/exams' },
            { label: 'Build paper' },
          ]}
          title="Build Exam Paper"
        />
        <ErrorPanel message={error} onRetry={loadExam}>
          <Button as={Link} to="/exams" variant="outline-secondary">
            Back to Exam List
          </Button>
        </ErrorPanel>
      </Box>
    )
  }

  const metaParts = [gradeName, subjectName].filter(Boolean)

  return (
    <Box>
      <PageHeader
        breadcrumbs={breadcrumbs}
        title="Build Exam Paper"
        description={[exam?.title, ...metaParts].filter(Boolean).join(' · ')}
        actions={
          <Button as={Link} to={selectQuestionsPath} variant="outline">
            Add Questions
          </Button>
        }
      />

      {isDirty && (
        <Alert variant="warning" className="mb-3 py-2">
          You have unsaved changes. Save before previewing or leaving this page.
        </Alert>
      )}

      <Card>
        <CardBody className="sc-card-body">
          {placements.length === 0 ? (
            <EmptyState
              title="No questions on this paper yet"
              description="Add questions from the bank, then drag to set the order."
              action={
                <Button as={Link} to={selectQuestionsPath}>
                  Add Questions
                </Button>
              }
            />
          ) : (
            <ReactSortable
              tag="ul"
              className="list-unstyled mb-0"
              list={placements}
              setList={(next) => {
                setPlacements(next)
                setSaveError(null)
                setSaveStatus('idle')
              }}
              handle=".drag-handle"
              disabled={saveStatus === 'saving'}
              animation={150}
            >
              {placements.map((placement, index) => {
                const question = placement.question || {}
                const labelNames = labelsText(question.labels)
                const typeLabel =
                  QUESTION_TYPE_LABELS[question.question_type] ||
                  question.question_type ||
                  '—'
                const marks = Number(question.marks) || 0
                const marksLabel = `${marks} mark${marks === 1 ? '' : 's'}`

                return (
                  <li key={placement.id} className="border-bottom py-3">
                    <Box className="d-flex flex-wrap align-items-start justify-content-between gap-3">
                      <Box className="d-flex align-items-start gap-2 flex-grow-1 min-w-0">
                        <button
                          type="button"
                          className="drag-handle btn btn-link btn-sm text-muted px-1 py-0 lh-1"
                          style={{ cursor: 'grab', userSelect: 'none' }}
                          aria-label={`Drag to reorder question ${index + 1}`}
                          disabled={saveStatus === 'saving'}
                        >
                          ⋮⋮
                        </button>
                        <Box className="flex-grow-1 min-w-0">
                          <p className="mb-1 fw-medium">
                            Q{index + 1}. {question.text || '—'}
                          </p>
                          <p className="mb-0 small text-muted">
                            {typeLabel}
                            <span className="mx-1">·</span>
                            {marksLabel}
                            {labelNames ? (
                              <>
                                <span className="mx-1">·</span>
                                {labelNames}
                              </>
                            ) : null}
                          </p>
                        </Box>
                      </Box>

                      <Box className="d-flex flex-wrap gap-2 flex-shrink-0">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline-secondary"
                          disabled={saveStatus === 'saving'}
                          onClick={() => removePlacement(placement.id)}
                        >
                          Remove
                        </Button>
                      </Box>
                    </Box>
                  </li>
                )
              })}
            </ReactSortable>
          )}

          {placements.length > 0 && (
            <>
              <hr className="my-4" />

              <Box className="d-flex flex-wrap gap-4 mb-4">
                <Box>
                  <span className="text-muted">Questions: </span>
                  <span className="fw-semibold">{questionCount}</span>
                </Box>
                <Box>
                  <span className="text-muted">Total Marks: </span>
                  <span className="fw-semibold">{totalMarks}</span>
                </Box>
              </Box>

              {saveError && (
                <Alert variant="danger" className="mb-3">
                  {saveError}
                </Alert>
              )}

              {saveStatus === 'saved' && !isDirty && (
                <Alert variant="success" className="mb-3">
                  Changes saved.
                </Alert>
              )}

              <Box className="d-flex flex-wrap gap-2">
                <Button
                  type="button"
                  disabled={!isDirty || saveStatus === 'saving'}
                  onClick={handleSave}
                >
                  {saveStatus === 'saving' ? 'Saving…' : 'Save Changes'}
                </Button>
                <Button
                  type="button"
                  variant="outline-secondary"
                  disabled={saveStatus === 'saving' || isDirty}
                  onClick={handlePreview}
                  title={
                    isDirty ? 'Save changes before previewing' : undefined
                  }
                >
                  Preview Paper
                </Button>
              </Box>
            </>
          )}

          {placements.length === 0 && removedIds.size > 0 && (
            <Box className="mt-4 pt-3 border-top">
              {saveError && (
                <Alert variant="danger" className="mb-3">
                  {saveError}
                </Alert>
              )}
              <Button
                type="button"
                disabled={saveStatus === 'saving'}
                onClick={handleSave}
              >
                {saveStatus === 'saving' ? 'Saving…' : 'Save Changes'}
              </Button>
            </Box>
          )}
        </CardBody>
      </Card>
    </Box>
  )
}
