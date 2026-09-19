import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { addExamQuestions, getExam } from '../../api/exams'
import { listLabels } from '../../api/labels'
import { getQuestionGenerationJob } from '../../api/questionGeneration'
import { listQuestions } from '../../api/questions'
import { useCatalog } from '../../contexts/CatalogContext'
import {
  buildListParams,
  DEFAULT_PAGE_SIZE,
  parsePaginatedResponse,
} from '../../utils/pagination'
import {
  Alert,
  Box,
  Button,
  Card,
  CardBody,
  Input,
  Pagination,
  Select,
  Spinner,
} from '../common_ui'
import QuestionFormDrawer from './QuestionFormDrawer'

const TYPE_LABELS = {
  mcq: 'MCQ',
  short: 'Short',
  long: 'Long',
}

const SEARCH_DEBOUNCE_MS = 300
const JOB_POLL_INTERVAL_MS = 2000

function truncate(text, max = 80) {
  const value = String(text || '').trim()
  if (value.length <= max) return value
  return `${value.slice(0, max - 1)}…`
}

function labelsText(labels) {
  if (!labels?.length) return '—'
  return labels.map((label) => label.name).join(', ')
}

function createdByLabel(createdBy) {
  if (!createdBy) return '—'
  const name = String(createdBy.first_name || '').trim()
  return name || createdBy.email || '—'
}

export default function QuestionBank() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { user, grades, subjects } = useCatalog()

  const isSelectMode = searchParams.get('mode') === 'select'
  const examId = searchParams.get('examId')
  const jobId = searchParams.get('jobId')

  const [exam, setExam] = useState(null)
  const [examStatus, setExamStatus] = useState(
    isSelectMode ? 'loading' : 'ready',
  )
  const [examError, setExamError] = useState(null)

  const [jobStatus, setJobStatus] = useState(jobId ? 'loading' : 'idle')
  const [jobError, setJobError] = useState(null)
  const [jobReady, setJobReady] = useState(!jobId)
  const [generatedCount, setGeneratedCount] = useState(null)

  const [questions, setQuestions] = useState([])
  const [labels, setLabels] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [subjectFilter, setSubjectFilter] = useState('')
  const [gradeFilter, setGradeFilter] = useState('')
  const [labelFilter, setLabelFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [difficultyFilter, setDifficultyFilter] = useState('')

  const [page, setPage] = useState(1)
  const [pageSize] = useState(DEFAULT_PAGE_SIZE)
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(1)

  // id → marks (keeps selection across pages in select mode)
  const [selectedMap, setSelectedMap] = useState(() => new Map())
  const [submitStatus, setSubmitStatus] = useState('idle')
  const [submitError, setSubmitError] = useState(null)

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerMode, setDrawerMode] = useState('create')
  const [editingQuestion, setEditingQuestion] = useState(null)

  const isJobMode = Boolean(jobId)
  const isGenerating =
    isJobMode && (jobStatus === 'loading' || jobStatus === 'pending' || jobStatus === 'running')

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

  // Poll generation job when arriving with ?jobId=
  useEffect(() => {
    if (!jobId) {
      setJobStatus('idle')
      setJobError(null)
      setJobReady(true)
      setGeneratedCount(null)
      return undefined
    }

    let cancelled = false
    let timerId

    setJobReady(false)
    setJobStatus('loading')
    setJobError(null)
    setGeneratedCount(null)
    setQuestions([])
    setPage(1)

    async function poll() {
      try {
        const { data } = await getQuestionGenerationJob(jobId)
        if (cancelled) return

        setSubjectFilter(String(data.subject ?? ''))
        setGradeFilter(String(data.grade ?? ''))
        setDifficultyFilter(String(data.difficulty ?? ''))
        setJobStatus(data.status)

        if (data.status === 'completed') {
          setJobError(null)
          setGeneratedCount(data.question_ids?.length ?? 0)
          setJobReady(true)
          return
        }

        if (data.status === 'failed') {
          setJobError(data.error_message || 'Question generation failed')
          setJobReady(false)
          return
        }

        timerId = setTimeout(poll, JOB_POLL_INTERVAL_MS)
      } catch (err) {
        if (cancelled) return
        setJobStatus('error')
        setJobReady(false)
        setJobError(
          err.response?.data?.detail ||
            err.response?.data?.error ||
            err.message ||
            'Failed to check generation status',
        )
      }
    }

    poll()

    return () => {
      cancelled = true
      clearTimeout(timerId)
    }
  }, [jobId])

  // Load exam when entering selection mode
  useEffect(() => {
    if (!isSelectMode) {
      setExam(null)
      setExamStatus('ready')
      setExamError(null)
      setSelectedMap(new Map())
      setSubmitError(null)
      setSubmitStatus('idle')
      if (!jobId) {
        setSubjectFilter('')
        setGradeFilter('')
      }
      return undefined
    }

    if (!examId) {
      setExam(null)
      setExamStatus('error')
      setExamError('Missing exam id. Create an exam first.')
      return undefined
    }

    let cancelled = false

    async function loadExam() {
      setExamStatus('loading')
      setExamError(null)
      try {
        const { data } = await getExam(examId)
        if (cancelled) return
        setExam(data)
        setSubjectFilter(String(data.subject ?? ''))
        setGradeFilter(String(data.grade ?? ''))
        setExamStatus('ready')
      } catch (err) {
        if (cancelled) return
        setExam(null)
        setExamStatus('error')
        setExamError(
          err.response?.data?.detail ||
            err.response?.data?.error ||
            err.message ||
            'Failed to load exam',
        )
      }
    }

    loadExam()
    return () => {
      cancelled = true
    }
  }, [isSelectMode, examId, jobId])

  // Debounce search text before hitting the API
  useEffect(() => {
    const timer = setTimeout(() => {
      const next = searchInput.trim()
      if (next === search) return
      setSearch(next)
      setPage(1)
    }, SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchInput, search])

  const loadQuestions = useCallback(
    async ({ silent = false } = {}) => {
      if (isSelectMode && examStatus !== 'ready') return
      if (isJobMode && !jobReady) return

      if (!silent) {
        setStatus('loading')
        setError(null)
      }

      const params = buildListParams({
        page,
        pageSize,
        search,
        grade: gradeFilter,
        subject: subjectFilter,
        label: labelFilter,
        question_type: typeFilter,
        difficulty: difficultyFilter,
        generation_job: jobId || undefined,
      })

      try {
        const { data } = await listQuestions(params)
        const pageData = parsePaginatedResponse(data, { page, pageSize })
        setQuestions(pageData.results)
        setTotalCount(pageData.count)
        setTotalPages(pageData.totalPages)
        setStatus('ready')
        setError(null)
      } catch (err) {
        const message =
          err.response?.data?.detail ||
          err.response?.data?.error ||
          err.message ||
          'Failed to load questions'
        setError(message)
        setStatus('error')
      }
    },
    [
      isSelectMode,
      examStatus,
      isJobMode,
      jobReady,
      jobId,
      page,
      pageSize,
      search,
      gradeFilter,
      subjectFilter,
      labelFilter,
      typeFilter,
      difficultyFilter,
    ],
  )

  function clearJobFilter() {
    const next = new URLSearchParams(searchParams)
    next.delete('jobId')
    setSearchParams(next, { replace: true })
    setJobStatus('idle')
    setJobError(null)
    setJobReady(true)
    setGeneratedCount(null)
    setPage(1)
  }

  const loadLabels = useCallback(async () => {
    try {
      const { data } = await listLabels()
      setLabels(Array.isArray(data) ? data : [])
    } catch {
      setLabels([])
    }
  }, [])

  useEffect(() => {
    loadLabels()
  }, [loadLabels])

  useEffect(() => {
    loadQuestions()
  }, [loadQuestions])

  // In normal mode, drop selections that left the current page.
  // In select mode, keep selections across pages.
  useEffect(() => {
    if (isSelectMode) return
    setSelectedMap((prev) => {
      const ids = new Set(questions.map((q) => q.id))
      const next = new Map()
      for (const [id, marks] of prev) {
        if (ids.has(id)) next.set(id, marks)
      }
      return next.size === prev.size ? prev : next
    })
  }, [questions, isSelectMode])

  const selectedIds = useMemo(
    () => new Set(selectedMap.keys()),
    [selectedMap],
  )

  const selectedCount = selectedMap.size
  const selectedMarks = useMemo(() => {
    let total = 0
    for (const marks of selectedMap.values()) total += Number(marks) || 0
    return total
  }, [selectedMap])

  const allVisibleSelected =
    questions.length > 0 &&
    questions.every((question) => selectedIds.has(question.id))

  function changeFilter(setter) {
    return (event) => {
      setter(event.target.value)
      setPage(1)
    }
  }

  function toggleSelectAll(checked) {
    setSelectedMap((prev) => {
      const next = new Map(prev)
      if (checked) {
        questions.forEach((question) => next.set(question.id, question.marks))
      } else {
        questions.forEach((question) => next.delete(question.id))
      }
      return next
    })
  }

  function toggleSelectOne(question, checked) {
    setSelectedMap((prev) => {
      const next = new Map(prev)
      if (checked) next.set(question.id, question.marks)
      else next.delete(question.id)
      return next
    })
  }

  function clearSelection() {
    setSelectedMap(new Map())
    setSubmitError(null)
  }

  async function handleAddToExam() {
    if (!examId || selectedCount === 0) return

    setSubmitStatus('submitting')
    setSubmitError(null)

    try {
      await addExamQuestions(examId, {
        question_ids: [...selectedMap.keys()],
      })
      setSubmitStatus('success')
      navigate(`/exams/${encodeURIComponent(examId)}/build`)
    } catch (err) {
      setSubmitStatus('error')
      setSubmitError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          err.response?.data?.question_ids?.[0] ||
          err.message ||
          'Failed to add questions to exam',
      )
    }
  }

  function openCreate() {
    setDrawerMode('create')
    setEditingQuestion(null)
    setDrawerOpen(true)
  }

  function openEdit(question) {
    const isOwner = question.created_by?.id === user?.id
    setDrawerMode(isOwner ? 'edit' : 'view')
    setEditingQuestion(question)
    setDrawerOpen(true)
  }

  function handleSaved() {
    setDrawerOpen(false)
    loadQuestions({ silent: true })
  }

  function handleLabelCreated(label) {
    setLabels((prev) => {
      if (prev.some((item) => item.id === label.id)) return prev
      return [...prev, label].sort((a, b) => a.name.localeCompare(b.name))
    })
  }

  const hasActiveFilters = Boolean(
    search ||
      (!isSelectMode && gradeFilter) ||
      (!isSelectMode && subjectFilter) ||
      labelFilter ||
      typeFilter ||
      difficultyFilter ||
      jobId,
  )

  if (isSelectMode && examStatus === 'loading') {
    return (
      <Box className="d-flex align-items-center gap-2 py-5 justify-content-center">
        <Spinner label="Loading exam…" />
        <span className="text-muted">Loading exam…</span>
      </Box>
    )
  }

  const builderPath = examId
    ? `/exams/${encodeURIComponent(examId)}/build`
    : '/exams'

  if (isSelectMode && examStatus === 'error') {
    return (
      <Box>
        <Button as={Link} to="/exams" variant="link" className="px-0 mb-3">
          ← Back to Exam List
        </Button>
        <Alert variant="danger" className="mb-3">
          {examError}
        </Alert>
        <Button as={Link} to="/exams/create">
          Create exam
        </Button>
      </Box>
    )
  }

  if (isJobMode && (jobStatus === 'failed' || jobStatus === 'error')) {
    return (
      <Box>
        <Box className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
          <h1 className="h4 mb-0">Question Bank</h1>
          <Button as={Link} to="/exams/generate" variant="outline-secondary">
            + Generate Questions
          </Button>
        </Box>
        <Alert variant="danger" className="mb-3">
          {jobError || 'Question generation failed'}
        </Alert>
        <Box className="d-flex flex-wrap gap-2">
          <Button as={Link} to="/exams/generate">
            Try again
          </Button>
          <Button type="button" variant="outline-secondary" onClick={clearJobFilter}>
            View all questions
          </Button>
        </Box>
      </Box>
    )
  }

  const filtersDisabled = isGenerating
  const tableColSpan = isSelectMode ? 5 : 6
  const showTable =
    isGenerating ||
    status === 'loading' ||
    (status === 'ready' && questions.length > 0)

  return (
    <Box className={isSelectMode ? 'pb-5 mb-4' : undefined}>
      {isSelectMode ? (
        <Box className="mb-4">
          <Button
            as={Link}
            to={builderPath}
            variant="link"
            className="px-0 mb-2"
          >
            ← Back to Paper Builder
          </Button>
          <h1 className="h4 mb-1">Select Questions</h1>
          <p className="text-muted mb-2">
            {[exam?.title, gradeName].filter(Boolean).join(' · ')}
            {subjectName ? ` · ${subjectName}` : ''}
          </p>
          <p className="small mb-0">
            <span className="fw-semibold">{selectedCount}</span> question
            {selectedCount === 1 ? '' : 's'} selected
            <span className="text-muted"> · </span>
            <span className="fw-semibold">{selectedMarks}</span> marks
          </p>
        </Box>
      ) : (
        <Box className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
          <h1 className="h4 mb-0">Question Bank</h1>
          <Box className="d-flex flex-wrap gap-2">
            <Button
              as={Link}
              to="/exams/generate"
              variant="outline-secondary"
              disabled={isGenerating}
            >
              + Generate Questions
            </Button>
            <Button type="button" onClick={openCreate} disabled={isGenerating}>
              + Add Question
            </Button>
          </Box>
        </Box>
      )}

      <Card className={isSelectMode ? 'border-primary border-opacity-25' : undefined}>
        <CardBody className="p-4">
          {isSelectMode && (
            <Alert variant="info" className="mb-3 py-2">
              Selection mode — choose questions for this exam, then continue.
            </Alert>
          )}

          <Box className="mb-3">
            <Input
              type="search"
              placeholder="Search questions…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              aria-label="Search questions"
              disabled={filtersDisabled}
            />
          </Box>

          <Box className="row g-2 mb-3">
            {!isSelectMode && (
              <>
                <Box className="col-6 col-md">
                  <Select
                    value={subjectFilter}
                    onChange={changeFilter(setSubjectFilter)}
                    aria-label="Filter by subject"
                    disabled={filtersDisabled}
                  >
                    <option value="">Subject</option>
                    {subjects.map((subject) => (
                      <option key={subject.id} value={subject.id}>
                        {subject.name}
                      </option>
                    ))}
                  </Select>
                </Box>
                <Box className="col-6 col-md">
                  <Select
                    value={gradeFilter}
                    onChange={changeFilter(setGradeFilter)}
                    aria-label="Filter by class"
                    disabled={filtersDisabled}
                  >
                    <option value="">Class</option>
                    {grades.map((grade) => (
                      <option key={grade.id} value={grade.id}>
                        {grade.name}
                      </option>
                    ))}
                  </Select>
                </Box>
              </>
            )}
            <Box className="col-6 col-md">
              <Select
                value={labelFilter}
                onChange={changeFilter(setLabelFilter)}
                aria-label="Filter by topic"
                disabled={filtersDisabled}
              >
                <option value="">Topic</option>
                {labels.map((label) => (
                  <option key={label.id} value={label.id}>
                    {label.name}
                  </option>
                ))}
              </Select>
            </Box>
            <Box className="col-6 col-md">
              <Select
                value={typeFilter}
                onChange={changeFilter(setTypeFilter)}
                aria-label="Filter by type"
                disabled={filtersDisabled}
              >
                <option value="">Type</option>
                <option value="mcq">MCQ</option>
                <option value="short">Short</option>
                <option value="long">Long</option>
              </Select>
            </Box>
            <Box className="col-6 col-md">
              <Select
                value={difficultyFilter}
                onChange={changeFilter(setDifficultyFilter)}
                aria-label="Filter by difficulty"
                disabled={filtersDisabled}
              >
                <option value="">Difficulty</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </Select>
            </Box>
          </Box>

          {!isGenerating && status === 'error' && (
            <Box className="py-3">
              <Alert variant="danger" className="mb-3">
                {error}
              </Alert>
              <Button type="button" onClick={() => loadQuestions()}>
                Try again
              </Button>
            </Box>
          )}

          {!isGenerating && status === 'ready' && questions.length === 0 && (
            <p className="text-muted text-center py-5 mb-0">
              {isJobMode
                ? 'No questions were created for this generation job.'
                : hasActiveFilters
                  ? 'No questions match your search or filters.'
                  : isSelectMode
                    ? 'No questions available for this exam class and subject.'
                    : 'No questions yet. Add one or generate from Exam.'}
            </p>
          )}

          {showTable && (
            <>
              <Box className="table-responsive">
                <table className="table table-hover align-middle mb-0">
                  <thead>
                    <tr>
                      <th scope="col" style={{ width: '2.5rem' }}>
                        <input
                          className="form-check-input"
                          type="checkbox"
                          checked={allVisibleSelected}
                          onChange={(e) => toggleSelectAll(e.target.checked)}
                          aria-label="Select all questions on this page"
                          disabled={isGenerating || status !== 'ready'}
                        />
                      </th>
                      <th scope="col">Question</th>
                      <th scope="col" style={{ width: '6rem' }}>
                        Type
                      </th>
                      <th scope="col" style={{ width: '5rem' }}>
                        Marks
                      </th>
                      <th scope="col" style={{ minWidth: '8rem' }}>
                        Topics
                      </th>
                      {!isSelectMode && (
                        <th scope="col" style={{ minWidth: '7rem' }}>
                          Created by
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {isGenerating || status === 'loading' ? (
                      <tr>
                        <td colSpan={tableColSpan} className="border-0">
                          <Box
                            className="d-flex flex-column align-items-center justify-content-center gap-3 py-5"
                            aria-live="polite"
                            aria-busy="true"
                          >
                            <Spinner
                              label={
                                isGenerating
                                  ? 'Question generating…'
                                  : 'Loading questions…'
                              }
                            />
                            <span className="text-muted">
                              {isGenerating
                                ? 'Question generating…'
                                : 'Loading questions…'}
                            </span>
                          </Box>
                        </td>
                      </tr>
                    ) : (
                      questions.map((question) => (
                        <tr
                          key={question.id}
                          className={
                            selectedIds.has(question.id)
                              ? 'table-active'
                              : undefined
                          }
                        >
                          <td>
                            <input
                              className="form-check-input"
                              type="checkbox"
                              checked={selectedIds.has(question.id)}
                              onChange={(e) =>
                                toggleSelectOne(question, e.target.checked)
                              }
                              aria-label={`Select question ${question.id}`}
                            />
                          </td>
                          <td>
                            {isSelectMode ? (
                              truncate(question.text)
                            ) : (
                              <button
                                type="button"
                                className="btn btn-link link-dark text-start text-decoration-none p-0"
                                onClick={() => openEdit(question)}
                              >
                                {truncate(question.text)}
                              </button>
                            )}
                          </td>
                          <td>
                            {TYPE_LABELS[question.question_type] ||
                              question.question_type}
                          </td>
                          <td>{question.marks}</td>
                          <td className="text-muted small">
                            {labelsText(question.labels)}
                          </td>
                          {!isSelectMode && (
                            <td>
                              <span className="badge text-bg-light border">
                                {createdByLabel(question.created_by)}
                              </span>
                            </td>
                          )}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </Box>

              {!isGenerating && status === 'ready' && questions.length > 0 && (
                <Pagination
                  className="mt-3"
                  page={page}
                  totalPages={totalPages}
                  count={totalCount}
                  pageSize={pageSize}
                  onChange={setPage}
                />
              )}
            </>
          )}

          {isJobMode && jobReady && (
            <Alert
              variant="success"
              className="mt-3 mb-0 py-2 d-flex flex-wrap align-items-center justify-content-between gap-2"
            >
              <span>
                Generated{' '}
                {generatedCount ?? totalCount} question
                {(generatedCount ?? totalCount) === 1 ? '' : 's'} successfully.
              </span>
              <Button
                type="button"
                size="sm"
                variant="outline-secondary"
                onClick={clearJobFilter}
              >
                View all questions
              </Button>
            </Alert>
          )}
        </CardBody>
      </Card>

      {isSelectMode && (
        <Box
          className="position-fixed bottom-0 end-0 border-top bg-white shadow-sm"
          style={{ zIndex: 1030, left: 220 }}
        >
          <Box className="d-flex flex-wrap align-items-center justify-content-between gap-3 px-4 py-3">
            <Box>
              <span className="fw-semibold">{selectedCount}</span> question
              {selectedCount === 1 ? '' : 's'} selected
              <span className="text-muted mx-2">·</span>
              Total marks: <span className="fw-semibold">{selectedMarks}</span>
              {submitError && (
                <Alert variant="danger" className="mb-0 mt-2 py-1 px-2 small">
                  {submitError}
                </Alert>
              )}
            </Box>
            <Box className="d-flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline-secondary"
                disabled={selectedCount === 0 || submitStatus === 'submitting'}
                onClick={clearSelection}
              >
                Clear Selection
              </Button>
              <Button
                type="button"
                disabled={selectedCount === 0 || submitStatus === 'submitting'}
                onClick={handleAddToExam}
              >
                {submitStatus === 'submitting' ? 'Adding…' : 'Continue →'}
              </Button>
            </Box>
          </Box>
        </Box>
      )}

      {!isSelectMode && (
        <QuestionFormDrawer
          open={drawerOpen}
          mode={drawerMode}
          question={editingQuestion}
          labels={labels}
          onClose={() => setDrawerOpen(false)}
          onSaved={handleSaved}
          onLabelsChange={handleLabelCreated}
        />
      )}
    </Box>
  )
}
