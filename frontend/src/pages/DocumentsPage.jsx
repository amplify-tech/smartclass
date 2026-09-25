import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listDocuments } from '../api/documents'
import {
  Box,
  Button,
  Card,
  CardBody,
  EmptyState,
  ErrorPanel,
  LoadingBlock,
  PageHeader,
  StatusBadge,
} from '../components/common_ui'
import { useCatalog } from '../contexts/CatalogContext'
import { getApiErrorMessage } from '../utils/apiErrors'
import {
  DOC_TYPE_LABELS,
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_STATUS_TONES,
} from '../utils/documentLabels'
import { formatDateTime } from '../utils/formatDate'
import { parsePaginatedResponse } from '../utils/pagination'

export default function DocumentsPage() {
  const { grades, subjects } = useCatalog()
  const [documents, setDocuments] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function loadDocuments() {
      setStatus('loading')
      setError(null)
      try {
        const { data } = await listDocuments()
        if (cancelled) return
        setDocuments(parsePaginatedResponse(data).results)
        setStatus('ready')
      } catch (err) {
        if (cancelled) return
        setDocuments([])
        setError(getApiErrorMessage(err, 'Failed to load documents'))
        setStatus('error')
      }
    }

    loadDocuments()
    return () => {
      cancelled = true
    }
  }, [])

  const gradeLabel = (id) =>
    grades.find((g) => Number(g.id) === Number(id))?.name || '—'

  const subjectLabel = (id) =>
    subjects.find((s) => Number(s.id) === Number(id))?.name || '—'

  const retry = () => {
    setStatus('loading')
    setError(null)
    listDocuments()
      .then(({ data }) => {
        setDocuments(parsePaginatedResponse(data).results)
        setStatus('ready')
      })
      .catch((err) => {
        setDocuments([])
        setError(getApiErrorMessage(err, 'Failed to load documents'))
        setStatus('error')
      })
  }

  return (
    <Box>
      <PageHeader
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'Documents' },
        ]}
        title="Documents"
        description="Upload and organize teaching documents."
        actions={
          <Button as={Link} to="/documents/upload">
            Upload Document
          </Button>
        }
      />

      <Card>
        <CardBody className="sc-card-body">
          {status === 'loading' && <LoadingBlock label="Loading documents…" />}

          {status === 'error' && (
            <ErrorPanel message={error} onRetry={retry} />
          )}

          {status === 'ready' && documents.length === 0 && (
            <EmptyState
              title="No documents yet"
              description="Upload a PDF to add it to your teaching materials."
              action={
                <Button as={Link} to="/documents/upload">
                  Upload Document
                </Button>
              }
            />
          )}

          {status === 'ready' && documents.length > 0 && (
            <Box className="table-responsive">
              <table className="table table-hover align-middle mb-0 sc-table">
                <thead>
                  <tr>
                    <th scope="col">Title</th>
                    <th scope="col">Grade</th>
                    <th scope="col">Subject</th>
                    <th scope="col">Type</th>
                    <th scope="col">Status</th>
                    <th scope="col">Uploaded</th>
                    <th scope="col" className="text-end">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td className="fw-medium">{doc.title || '—'}</td>
                      <td>{gradeLabel(doc.grade)}</td>
                      <td>{subjectLabel(doc.subject)}</td>
                      <td>
                        {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type || '—'}
                      </td>
                      <td>
                        <StatusBadge
                          tone={
                            DOCUMENT_STATUS_TONES[doc.status] || 'secondary'
                          }
                        >
                          {DOCUMENT_STATUS_LABELS[doc.status] ||
                            doc.status ||
                            '—'}
                        </StatusBadge>
                      </td>
                      <td className="text-nowrap small text-muted">
                        {formatDateTime(doc.created_at)}
                      </td>
                      <td className="text-end text-nowrap">
                        {doc.file_url ? (
                          <Button
                            as="a"
                            href={doc.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            size="sm"
                            variant="outline"
                          >
                            View
                          </Button>
                        ) : (
                          <span className="text-muted small">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Box>
          )}
        </CardBody>
      </Card>
    </Box>
  )
}
