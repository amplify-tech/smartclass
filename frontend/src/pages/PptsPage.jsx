import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { listConversations } from '../api/presentations'
import {
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

export default function PptsPage() {
  const [chats, setChats] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    listConversations({ page_size: 100 })
      .then(({ data }) => {
        if (cancelled) return
        setChats(parsePaginatedResponse(data).results)
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setError(getApiErrorMessage(err, 'Failed to load chats'))
        setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [reloadKey])

  function retry() {
    setStatus('loading')
    setReloadKey((n) => n + 1)
  }

  const newChat = (
    <Button as={Link} to="/ppts/chat/new">
      New chat
    </Button>
  )

  return (
    <Box>
      <PageHeader
        breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'PPT' }]}
        title="PPT"
        description="Create and edit Google Slides presentations by chatting."
        actions={newChat}
      />

      <Card>
        <CardBody className="sc-card-body">
          {status === 'loading' && <LoadingBlock label="Loading chats…" />}

          {status === 'error' && <ErrorPanel message={error} onRetry={retry} />}

          {status === 'ready' && chats.length === 0 && (
            <EmptyState
              title="No chats yet"
              description="Start a chat and ask for a presentation, e.g. a 3-slide PPT on Optics."
              action={newChat}
            />
          )}

          {status === 'ready' && chats.length > 0 && (
            <Box className="list-group list-group-flush">
              {chats.map((chat) => (
                <Link
                  key={chat.id}
                  to={`/ppts/chat/${chat.id}`}
                  className="list-group-item list-group-item-action d-flex justify-content-between gap-3"
                >
                  <span className="fw-medium text-truncate">{chat.title || 'Untitled chat'}</span>
                  <span className="small text-muted text-nowrap">
                    {formatDateTime(chat.updated_at)}
                  </span>
                </Link>
              ))}
            </Box>
          )}
        </CardBody>
      </Card>
    </Box>
  )
}
