import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getExam } from '../api/exams'
import ExamPrintPreview from '../components/exams/ExamPrintPreview'
import {
  Box,
  Button,
  ErrorPanel,
  LoadingBlock,
  PageHeader,
} from '../components/common_ui'
import { useCatalog } from '../contexts/CatalogContext'
import { getApiErrorMessage } from '../utils/apiErrors'

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
      setError(getApiErrorMessage(err, 'Failed to load exam'))
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

  const editPath = examId
    ? `/exams/${encodeURIComponent(examId)}/build`
    : '/exams'

  const breadcrumbs = [
    { label: 'Home', to: '/' },
    { label: 'Exams', to: '/exams' },
    {
      label: exam?.title || 'Exam',
      to: editPath,
    },
    { label: 'Preview' },
  ]

  if (status === 'loading') {
    return (
      <Box className="d-print-none">
        <PageHeader breadcrumbs={breadcrumbs} title="Exam Preview" />
        <LoadingBlock label="Loading exam preview…" />
      </Box>
    )
  }

  if (status === 'error') {
    return (
      <Box className="d-print-none">
        <PageHeader breadcrumbs={breadcrumbs} title="Exam Preview" />
        <ErrorPanel message={error} onRetry={loadExam}>
          <Button as={Link} to={editPath} variant="outline-secondary">
            Edit Exam
          </Button>
        </ErrorPanel>
      </Box>
    )
  }

  return (
    <Box>
      <Box className="d-print-none">
        <PageHeader
          breadcrumbs={breadcrumbs}
          title="Exam Preview"
          description="Print or save as PDF from your browser print dialog."
          actions={
            <Box className="d-flex flex-wrap gap-2">
              <Button as={Link} to={editPath} variant="outline-secondary">
                Edit Exam
              </Button>
              <Button
                type="button"
                variant="outline-secondary"
                onClick={() => window.print()}
                title='Opens print dialog — choose "Save as PDF"'
              >
                Download PDF
              </Button>
              <Button type="button" onClick={() => window.print()}>
                Print
              </Button>
            </Box>
          }
        />
      </Box>

      <ExamPrintPreview
        exam={exam}
        gradeName={gradeName}
        subjectName={subjectName}
      />
    </Box>
  )
}
