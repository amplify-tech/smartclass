import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createChat } from '../api/chat'
import { listPresentations } from '../api/presentations'
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
} from '../components/common_ui'
import { getApiErrorMessage } from '../utils/apiErrors'
import { formatDateTime } from '../utils/formatDate'
import { parsePaginatedResponse } from '../utils/pagination'
import { presentationChat, presentationChatContext } from './presentationChat'

export default function PptsPage() {
  const navigate = useNavigate()
  const [presentations, setPresentations] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [chatError, setChatError] = useState(null)
  const [creatingChat, setCreatingChat] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function loadPresentations() {
      setStatus('loading')
      setError(null)
      try {
        const { data } = await listPresentations()
        if (cancelled) return
        setPresentations(parsePaginatedResponse(data).results)
        setStatus('ready')
      } catch (err) {
        if (cancelled) return
        setPresentations([])
        setError(getApiErrorMessage(err, 'Failed to load presentations'))
        setStatus('error')
      }
    }

    loadPresentations()
    return () => {
      cancelled = true
    }
  }, [])

  const retry = () => {
    setStatus('loading')
    setError(null)
    listPresentations()
      .then(({ data }) => {
        setPresentations(parsePaginatedResponse(data).results)
        setStatus('ready')
      })
      .catch((err) => {
        setPresentations([])
        setError(getApiErrorMessage(err, 'Failed to load presentations'))
        setStatus('error')
      })
  }

  async function openNewChat(presentation = null) {
    const key = presentation?.id || 'new'
    if (creatingChat) return
    setCreatingChat(key)
    setChatError(null)
    try {
      const { data } = await createChat(
        presentationChat.chatType,
        presentationChatContext(presentation),
      )
      navigate(presentationChat.chatPath(data.id))
    } catch (err) {
      setChatError(getApiErrorMessage(err, 'Failed to create chat'))
    } finally {
      setCreatingChat(null)
    }
  }

  return (
    <Box>
      <PageHeader
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'PPT' },
        ]}
        title="PPT"
        description="Create and open Google Slides presentations."
        actions={
          <Button onClick={() => openNewChat()} disabled={Boolean(creatingChat)}>
            {creatingChat === 'new' ? 'Creating…' : 'New chat'}
          </Button>
        }
      />

      {chatError ? <Alert variant="danger">{chatError}</Alert> : null}

      <Card>
        <CardBody className="sc-card-body">
          {status === 'loading' && <LoadingBlock label="Loading presentations…" />}

          {status === 'error' && (
            <ErrorPanel message={error} onRetry={retry} />
          )}

          {status === 'ready' && presentations.length === 0 && (
            <EmptyState
              title="No presentations yet"
              description="Start a chat and ask for a presentation, e.g. a 3-slide PPT on Optics."
              action={
                <Button onClick={() => openNewChat()} disabled={Boolean(creatingChat)}>
                  {creatingChat === 'new' ? 'Creating…' : 'New chat'}
                </Button>
              }
            />
          )}

          {status === 'ready' && presentations.length > 0 && (
            <Box className="table-responsive">
              <table className="table table-hover align-middle mb-0 sc-table">
                <thead>
                  <tr>
                    <th scope="col">Title</th>
                    <th scope="col">Created</th>
                    <th scope="col">Updated</th>
                    <th scope="col" className="text-end">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {presentations.map((ppt) => (
                    <tr key={ppt.id}>
                      <td className="fw-medium">{ppt.title || '—'}</td>
                      <td className="text-nowrap small text-muted">
                        {formatDateTime(ppt.created_at)}
                      </td>
                      <td className="text-nowrap small text-muted">
                        {formatDateTime(ppt.updated_at)}
                      </td>
                      <td className="text-end text-nowrap">
                        <Button
                          size="sm"
                          variant="outline"
                          className="me-2"
                          onClick={() => openNewChat(ppt)}
                          disabled={Boolean(creatingChat)}
                        >
                          {creatingChat === ppt.id ? 'Creating…' : 'Chat'}
                        </Button>
                        {ppt.url ? (
                          <Button
                            as="a"
                            href={ppt.url}
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
