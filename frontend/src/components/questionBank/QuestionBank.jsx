import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listLabels } from '../../api/labels'
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

function truncate(text, max = 80) {
  const value = String(text || '').trim()
  if (value.length <= max) return value
  return `${value.slice(0, max - 1)}…`
}

function topicsText(labels) {
  if (!labels?.length) return '—'
  return labels.map((label) => label.name).join(', ')
}

function createdByLabel(createdBy) {
  if (!createdBy) return '—'
  const name = String(createdBy.first_name || '').trim()
  return name || createdBy.email || '—'
}

export default function QuestionBank() {
  const { user, grades, subjects } = useCatalog()

  const [questions, setQuestions] = useState([])
  const [labels, setLabels] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [subjectFilter, setSubjectFilter] = useState('')
  const [gradeFilter, setGradeFilter] = useState('')
  const [topicFilter, setTopicFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [difficultyFilter, setDifficultyFilter] = useState('')

  const [page, setPage] = useState(1)
  const [pageSize] = useState(DEFAULT_PAGE_SIZE)
  const [totalCount, setTotalCount] = useState(0)
  const [totalPages, setTotalPages] = useState(1)

  const [selectedIds, setSelectedIds] = useState(() => new Set())
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerMode, setDrawerMode] = useState('create')
  const [editingQuestion, setEditingQuestion] = useState(null)

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
        label: topicFilter,
        question_type: typeFilter,
        difficulty: difficultyFilter,
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
      page,
      pageSize,
      search,
      gradeFilter,
      subjectFilter,
      topicFilter,
      typeFilter,
      difficultyFilter,
    ],
  )

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

  // Drop selections that no longer exist on the current page
  useEffect(() => {
    setSelectedIds((prev) => {
      const ids = new Set(questions.map((q) => q.id))
      const next = new Set([...prev].filter((id) => ids.has(id)))
      return next.size === prev.size ? prev : next
    })
  }, [questions])

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
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (checked) {
        questions.forEach((question) => next.add(question.id))
      } else {
        questions.forEach((question) => next.delete(question.id))
      }
      return next
    })
  }

  function toggleSelectOne(id, checked) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (checked) next.add(id)
      else next.delete(id)
      return next
    })
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
      gradeFilter ||
      subjectFilter ||
      topicFilter ||
      typeFilter ||
      difficultyFilter,
  )

  return (
    <Box>
      <Box className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <h1 className="h4 mb-0">Question Bank</h1>
        <Box className="d-flex flex-wrap gap-2">
          <Button as={Link} to="/exams" variant="outline-secondary">
            + Generate Questions
          </Button>
          <Button type="button" onClick={openCreate}>
            + Add Question
          </Button>
        </Box>
      </Box>

      <Card>
        <CardBody className="p-4">
          <Box className="mb-3">
            <Input
              type="search"
              placeholder="Search questions…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              aria-label="Search questions"
            />
          </Box>

          <Box className="row g-2 mb-3">
            <Box className="col-6 col-md">
              <Select
                value={subjectFilter}
                onChange={changeFilter(setSubjectFilter)}
                aria-label="Filter by subject"
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
              >
                <option value="">Class</option>
                {grades.map((grade) => (
                  <option key={grade.id} value={grade.id}>
                    {grade.name}
                  </option>
                ))}
              </Select>
            </Box>
            <Box className="col-6 col-md">
              <Select
                value={topicFilter}
                onChange={changeFilter(setTopicFilter)}
                aria-label="Filter by topic"
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
              >
                <option value="">Difficulty</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </Select>
            </Box>
          </Box>

          {status === 'loading' && (
            <Box className="d-flex align-items-center gap-2 py-5 justify-content-center">
              <Spinner label="Loading questions…" />
              <span className="text-muted">Loading questions…</span>
            </Box>
          )}

          {status === 'error' && (
            <Box className="py-3">
              <Alert variant="danger" className="mb-3">
                {error}
              </Alert>
              <Button type="button" onClick={() => loadQuestions()}>
                Try again
              </Button>
            </Box>
          )}

          {status === 'ready' && questions.length === 0 && (
            <p className="text-muted text-center py-5 mb-0">
              {hasActiveFilters
                ? 'No questions match your search or filters.'
                : 'No questions yet. Add one or generate from Exam.'}
            </p>
          )}

          {status === 'ready' && questions.length > 0 && (
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
                      <th scope="col" style={{ minWidth: '7rem' }}>
                        Created by
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {questions.map((question) => (
                      <tr key={question.id}>
                        <td>
                          <input
                            className="form-check-input"
                            type="checkbox"
                            checked={selectedIds.has(question.id)}
                            onChange={(e) =>
                              toggleSelectOne(question.id, e.target.checked)
                            }
                            aria-label={`Select question ${question.id}`}
                          />
                        </td>
                        <td>
                          <button
                            type="button"
                            className="btn btn-link link-dark text-start text-decoration-none p-0"
                            onClick={() => openEdit(question)}
                          >
                            {truncate(question.text)}
                          </button>
                        </td>
                        <td>
                          {TYPE_LABELS[question.question_type] ||
                            question.question_type}
                        </td>
                        <td>{question.marks}</td>
                        <td className="text-muted small">
                          {topicsText(question.labels)}
                        </td>
                        <td>
                          <span className="badge text-bg-light border">
                            {createdByLabel(question.created_by)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>

              <Pagination
                className="mt-3"
                page={page}
                totalPages={totalPages}
                count={totalCount}
                pageSize={pageSize}
                onChange={setPage}
              />
            </>
          )}
        </CardBody>
      </Card>

      <QuestionFormDrawer
        open={drawerOpen}
        mode={drawerMode}
        question={editingQuestion}
        labels={labels}
        onClose={() => setDrawerOpen(false)}
        onSaved={handleSaved}
        onLabelsChange={handleLabelCreated}
      />
    </Box>
  )
}
