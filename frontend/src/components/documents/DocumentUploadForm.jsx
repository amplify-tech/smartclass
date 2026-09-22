import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'

import { createDocument } from '../../api/documents'
import { useCatalog } from '../../contexts/CatalogContext'
import {
  DOC_TYPE_LABELS,
  DOC_TYPE_OPTIONS,
  DOC_TYPE_VALUES,
  MAX_DOCUMENT_UPLOAD_BYTES,
  titleFromFilename,
} from '../../utils/documentLabels'
import {
  Box,
  Button,
  FormField,
  FormRootError,
  Select,
  Spinner,
} from '../common_ui'
import DocumentFilePicker from './DocumentFilePicker'

const schema = z.object({
  grade: z.coerce.number().int().positive('Select a grade'),
  subject: z.coerce.number().int().positive('Select a subject'),
  doc_type: z.enum(DOC_TYPE_VALUES, {
    message: 'Select a document type',
  }),
})

function validatePdfFile(file) {
  if (!file) return 'Choose a PDF file'
  const name = String(file.name || '').toLowerCase()
  const type = String(file.type || '').toLowerCase()
  const isPdf = type === 'application/pdf' || name.endsWith('.pdf')
  if (!isPdf) return 'Only PDF files are allowed'
  if (file.size > MAX_DOCUMENT_UPLOAD_BYTES) {
    const maxMb = MAX_DOCUMENT_UPLOAD_BYTES / (1024 * 1024)
    return `File too large. Maximum size is ${maxMb} MB.`
  }
  return null
}

/**
 * Document upload form with form → uploading → success | error states.
 * @param {(phase: 'form'|'uploading'|'success'|'error') => void} [onPhaseChange]
 */
export default function DocumentUploadForm({ onPhaseChange }) {
  const { grades, subjects } = useCatalog()
  const [phase, setPhase] = useState('form')
  const [file, setFile] = useState(null)
  const [fileError, setFileError] = useState(null)
  const [uploaded, setUploaded] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      grade: '',
      subject: '',
      doc_type: '',
    },
  })

  const updatePhase = (next) => {
    setPhase(next)
    onPhaseChange?.(next)
  }

  const busy = submitting || phase === 'uploading'
  const formDisabled = busy

  const handleFileChange = (next) => {
    setFile(next)
    setFileError(next ? validatePdfFile(next) : null)
  }

  const onSubmit = async (values) => {
    if (submitting) return

    const fileValidation = validatePdfFile(file)
    if (fileValidation) {
      setFileError(fileValidation)
      return
    }

    setSubmitting(true)
    updatePhase('uploading')

    const formData = new FormData()
    formData.append('title', titleFromFilename(file.name))
    formData.append('file', file)
    formData.append('doc_type', values.doc_type)
    formData.append('grade', String(values.grade))
    formData.append('subject', String(values.subject))

    try {
      const { data } = await createDocument(formData)
      const gradeName =
        grades.find((g) => Number(g.id) === Number(values.grade))?.name || null
      const subjectName =
        subjects.find((s) => Number(s.id) === Number(values.subject))?.name ||
        null
      const docTypeLabel = DOC_TYPE_LABELS[values.doc_type] || values.doc_type

      setUploaded({
        title: data?.title || titleFromFilename(file.name),
        fileName: file.name,
        gradeName,
        subjectName,
        docTypeLabel,
      })
      updatePhase('success')
    } catch {
      updatePhase('error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleTryAgain = () => {
    updatePhase('form')
  }

  if (phase === 'uploading') {
    return (
      <Box className="text-center py-4" aria-live="polite" aria-busy="true">
        <p className="mb-3 fw-medium text-truncate">
          <span aria-hidden="true" className="me-2">
            📄
          </span>
          {file?.name}
        </p>
        <Spinner label="Uploading…" className="mb-3" />
        <p className="mb-2 fw-semibold">Uploading…</p>
        <p className="text-muted mb-0">
          Please wait while your document is uploaded.
        </p>
      </Box>
    )
  }

  if (phase === 'success' && uploaded) {
    const meta = [uploaded.gradeName, uploaded.subjectName, uploaded.docTypeLabel]
      .filter(Boolean)
      .join(' • ')

    return (
      <Box className="text-center py-4" aria-live="polite">
        <p className="mb-1 fw-semibold">{uploaded.fileName || uploaded.title}</p>
        {meta ? <p className="text-muted mb-3">{meta}</p> : null}
        <p className="mb-4">Your document has been uploaded successfully.</p>
        <Button as={Link} to="/documents">
          View Documents
        </Button>
      </Box>
    )
  }

  if (phase === 'error') {
    return (
      <Box className="py-3" aria-live="polite">
        <p className="mb-3 text-muted">
          We couldn&apos;t upload the document.
          <br />
          Please try again.
        </p>
        <Button type="button" onClick={handleTryAgain}>
          Try Again
        </Button>
      </Box>
    )
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-busy={busy ? 'true' : undefined}
    >
      <DocumentFilePicker
        file={file}
        onChange={handleFileChange}
        error={fileError}
        disabled={formDisabled}
      />

      <Box className="row g-3">
        <FormField
          id="doc-grade"
          label="Grade"
          error={errors.grade?.message}
          className="col-md-4"
        >
          <Select disabled={formDisabled} {...register('grade')}>
            <option value="">Select grade</option>
            {grades.map((grade) => (
              <option key={grade.id} value={grade.id}>
                {grade.name}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField
          id="doc-subject"
          label="Subject"
          error={errors.subject?.message}
          className="col-md-4"
        >
          <Select disabled={formDisabled} {...register('subject')}>
            <option value="">Select subject</option>
            {subjects.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField
          id="doc-type"
          label="Document Type"
          error={errors.doc_type?.message}
          className="col-md-4"
        >
          <Select disabled={formDisabled} {...register('doc_type')}>
            <option value="">Select type</option>
            {DOC_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        </FormField>
      </Box>

      <FormRootError message={errors.root?.message} />

      <Box className="d-flex flex-wrap justify-content-end gap-2">
        <Button
          as={Link}
          to="/documents"
          variant="outline-secondary"
          disabled={formDisabled}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={formDisabled}>
          Upload
        </Button>
      </Box>
    </form>
  )
}
