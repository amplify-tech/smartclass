import { useEffect, useState } from 'react'

import { listDocuments } from '../../api/documents'
import { useCatalog } from '../../contexts/CatalogContext'
import { getApiErrorMessage } from '../../utils/apiErrors'
import {
  DOC_TYPE_LABELS,
  DOCUMENT_STATUS,
} from '../../utils/documentLabels'
import {
  buildListParams,
  parsePaginatedResponse,
} from '../../utils/pagination'
import {
  Box,
  Button,
  ErrorPanel,
  Input,
  LoadingBlock,
  Modal,
} from '../common_ui'
import { cx } from '../common_ui/cx'

const PAGE_SIZE = 12

/** Remount on open so list state starts clean. */
export default function DocumentSelectModal(props) {
  if (!props.open) return null
  return <DocumentSelectModalOpen {...props} />
}

function DocumentSelectModalOpen({
  onClose,
  value = null,
  onSelect,
  grade,
  subject,
  status: statusFilter = DOCUMENT_STATUS.READY,
  docType,
  title = 'Select document',
  description = 'Choose a document.',
}) {
  const { grades, subjects } = useCatalog()
  const [selected, setSelected] = useState(value)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [documents, setDocuments] = useState([])
  const [hasNext, setHasNext] = useState(false)
  const [hasPrevious, setHasPrevious] = useState(false)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const t = setTimeout(() => {
      const next = searchInput.trim()
      if (next === search) return
      setSearch(next)
      setPage(1)
    }, 300)
    return () => clearTimeout(t)
  }, [searchInput, search])

  useEffect(() => {
    let cancelled = false

    async function load() {
      setStatus('loading')
      setError(null)
      try {
        const { data } = await listDocuments(
          buildListParams({
            page,
            pageSize: PAGE_SIZE,
            search,
            grade,
            subject,
            status: statusFilter,
            doc_type: docType,
            ordering: '-updated_at',
          }),
        )
        if (cancelled) return
        const parsed = parsePaginatedResponse(data, { page, pageSize: PAGE_SIZE })
        setDocuments(parsed.results)
        setHasNext(parsed.hasNext)
        setHasPrevious(parsed.hasPrevious)
        setStatus('ready')
      } catch (err) {
        if (cancelled) return
        setDocuments([])
        setHasNext(false)
        setHasPrevious(false)
        setError(getApiErrorMessage(err, 'Failed to load documents'))
        setStatus('error')
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [grade, subject, statusFilter, docType, page, search, reloadKey])

  const nameOf = (list, id) =>
    list.find((item) => Number(item.id) === Number(id))?.name || '—'

  const shortDate = (v) => {
    if (!v) return '—'
    const d = new Date(v)
    return Number.isNaN(d.getTime())
      ? '—'
      : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  }

  const busy = status === 'loading'

  return (
    <Modal
      open
      onClose={onClose}
      size="lg"
      title={title}
      footer={
        <Button
          type="button"
          disabled={!selected}
          onClick={() => {
            onSelect?.(selected)
            onClose?.()
          }}
        >
          Select
        </Button>
      }
    >
      {description ? (
        <p className="text-muted small mb-3">{description}</p>
      ) : null}

      <Input
        type="search"
        className="mb-3"
        placeholder="Search documents..."
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        aria-label="Search documents"
      />

      {busy && <LoadingBlock label="Loading documents…" />}
      {status === 'error' && (
        <ErrorPanel message={error} onRetry={() => setReloadKey((k) => k + 1)} />
      )}
      {status === 'ready' && documents.length === 0 && (
        <p className="text-muted small py-4 mb-0 text-center">
          {search ? 'No documents match your search.' : 'No documents found.'}
        </p>
      )}
      {status === 'ready' && documents.length > 0 && (
        <Box className="table-responsive">
          <table className="table table-hover align-middle mb-0 sc-table">
            <thead>
              <tr>
                <th scope="col">Document</th>
                <th scope="col">Type</th>
                <th scope="col">Last Updated</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr
                  key={doc.id}
                  className={cx(selected?.id === doc.id && 'table-active')}
                  style={{ cursor: 'pointer' }}
                  onClick={() =>
                    setSelected((cur) => (cur?.id === doc.id ? null : doc))
                  }
                >
                  <td>
                    <p className="mb-0 fw-medium">
                      <span aria-hidden="true" className="me-2">
                        📄
                      </span>
                      {doc.title || '—'}
                    </p>
                    <p className="mb-0 small text-muted">
                      {nameOf(grades, doc.grade)} · {nameOf(subjects, doc.subject)}
                    </p>
                  </td>
                  <td className="text-nowrap">
                    {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type || '—'}
                  </td>
                  <td className="text-nowrap small text-muted">
                    {shortDate(doc.updated_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Box>
      )}

      <Box className="d-flex justify-content-between align-items-center gap-2 mt-3">
        <p className="mb-0 small text-muted">
          {selected ? `Selected: ${selected.title}` : 'No document selected'}
        </p>
        <Box className="d-flex gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline-secondary"
            disabled={!hasPrevious || busy}
            onClick={() => setPage((p) => p - 1)}
          >
            ‹ Previous
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline-secondary"
            disabled={!hasNext || busy}
            onClick={() => setPage((p) => p + 1)}
          >
            Next ›
          </Button>
        </Box>
      </Box>
    </Modal>
  )
}
