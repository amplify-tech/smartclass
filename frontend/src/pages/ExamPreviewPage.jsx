import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getExam } from '../api/exams'
import ExamPrintPreview from '../components/exams/ExamPrintPreview'
import {
  Alert,
  Box,
  Button,
  Spinner,
} from '../components/common_ui'
import { useCatalog } from '../contexts/CatalogContext'

export default function ExamPreviewPage() {
  const { examId } = useParams()
  const { grades, subjects } = useCatalog()

  const [exam, setExam] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)

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

  const loadExam = useCallback(async () => {
    setStatus('loading')
    setError(null)
    try {
      const { data } = await getExam(examId)
      setExam(data)
      setStatus('ready')
    } catch (err) {
      setExam(null)
      setError(
        err.response?.data?.detail ||
          err.response?.data?.error ||
          err.message ||
          'Failed to load exam',
      )
      setStatus('error')
    }
  }, [examId])

  useEffect(() => {
    loadExam()
  }, [loadExam])

  useEffect(() => {
    if (!exam?.title) return undefined
    const previous = document.title
    const parts = [exam.title, subjectName, gradeName].filter(Boolean)
    document.title = parts.join(' - ')
    return () => {
      document.title = previous
    }
  }, [exam?.title, subjectName, gradeName])

  const handlePrint = () => {
    window.print()
  }

  const handleDownloadPdf = () => {
    // Browser print dialog → choose "Save as PDF"
    window.print()
  }

  if (status === 'loading') {
    return (
      <Box className="d-flex align-items-center gap-2 py-5 justify-content-center d-print-none">
        <Spinner label="Loading exam preview…" />
        <span className="text-muted">Loading exam preview…</span>
      </Box>
    )
  }

  if (status === 'error') {
    return (
      <Box className="d-print-none">
        <Button
          as={Link}
          to={`/exams/${encodeURIComponent(examId)}/build`}
          variant="link"
          className="px-0 mb-3"
        >
          ← Edit Exam
        </Button>
        <Alert variant="danger" className="mb-3">
          {error}
        </Alert>
        <Button type="button" onClick={loadExam}>
          Try again
        </Button>
      </Box>
    )
  }

  const editPath = `/exams/${encodeURIComponent(examId)}/build`

  return (
    <ExamPrintPreview
      exam={exam}
      gradeName={gradeName}
      subjectName={subjectName}
      toolbar={
        <>
          <Button as={Link} to={editPath} variant="link" className="px-0">
            ← Edit Exam
          </Button>
          <Box className="exam-print-preview__toolbar-actions">
            <Button
              type="button"
              variant="outline-secondary"
              onClick={handleDownloadPdf}
              title='Opens print dialog — choose "Save as PDF"'
            >
              Download PDF
            </Button>
            <Button type="button" onClick={handlePrint}>
              Print
            </Button>
          </Box>
        </>
      }
    />
  )
}
