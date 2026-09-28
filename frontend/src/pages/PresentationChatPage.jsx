import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import {
  createConversation,
  getConversation,
  sendConversationMessage,
} from '../api/presentations'
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
  Spinner,
  Textarea,
  cx,
} from '../components/common_ui'
import { getApiErrorMessage } from '../utils/apiErrors'

const MAX_MESSAGE_LENGTH = 4000

export default function PresentationChatPage() {
  const { chatId } = useParams()
  return <ChatView key={chatId || 'new'} chatId={chatId} />
}

function ChatView({ chatId }) {
  const navigate = useNavigate()
  const location = useLocation()
  // A chat just started on /ppts/chat/new is handed over so it shows without a loading flash.
  const [conversation, setConversation] = useState(location.state?.conversation || null)
  const [status, setStatus] = useState(chatId && !conversation ? 'loading' : 'ready')
  const [loadError, setLoadError] = useState(null)
  const [text, setText] = useState('')
  const [sending, setSending] = useState(null)
  const [sendError, setSendError] = useState(null)
  const endRef = useRef(null)

  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    if (!chatId) return undefined
    let cancelled = false
    getConversation(chatId)
      .then(({ data }) => {
        if (cancelled) return
        setConversation(data)
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setLoadError(getApiErrorMessage(err, 'Failed to load chat'))
        setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [chatId, reloadKey])

  function retry() {
    setStatus('loading')
    setReloadKey((n) => n + 1)
  }

  const messages = conversation?.messages || []

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, sending])

  async function send() {
    const content = text.trim()
    if (!content || sending) return

    setSending(content)
    setSendError(null)
    setText('')
    try {
      const id = conversation?.id ?? (await createConversation()).data.id
      const { data } = await sendConversationMessage(id, content)
      setConversation(data)
      if (!chatId) {
        navigate(`/ppts/chat/${id}`, { replace: true, state: { conversation: data } })
      }
    } catch (err) {
      setText(content)
      setSendError(getApiErrorMessage(err, 'Failed to send message'))
    } finally {
      setSending(null)
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send()
    }
  }

  const title = conversation?.title || 'New chat'

  return (
    <Box>
      <PageHeader
        breadcrumbs={[
          { label: 'Home', to: '/' },
          { label: 'PPT', to: '/ppts' },
          { label: title },
        ]}
        title={title}
        description="Ask for a presentation, then keep chatting to change it."
        actions={
          <Button as={Link} to="/ppts/chat/new" variant="outline">
            New chat
          </Button>
        }
      />

      <Card>
        <CardBody className="sc-chat">
          {status === 'loading' && <LoadingBlock label="Loading chat…" />}

          {status === 'error' && <ErrorPanel message={loadError} onRetry={retry} />}

          {status === 'ready' && (
            <>
              <Box className="sc-chat__messages">
                {messages.length === 0 && !sending && (
                  <EmptyState
                    title="Start a new presentation"
                    description='For example: "Generate a 3-slide PPT on Class 6 Physics - Optics."'
                  />
                )}

                {messages.map((m) => (
                  <ChatMessage key={m.id} message={m} />
                ))}

                {sending && (
                  <>
                    <ChatMessage message={{ role: 'user', content: sending }} />
                    <Box className="sc-chat__bubble sc-chat__bubble--assistant d-flex align-items-center gap-2">
                      <Spinner size="sm" label="Working…" />
                      <span className="text-muted">Working on it…</span>
                    </Box>
                  </>
                )}
                <div ref={endRef} />
              </Box>

              {sendError && (
                <Alert variant="danger" className="mb-2">
                  {sendError}
                </Alert>
              )}

              <Box
                as="form"
                className="sc-chat__composer"
                onSubmit={(event) => {
                  event.preventDefault()
                  send()
                }}
              >
                <Textarea
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a message… (Enter to send, Shift+Enter for a new line)"
                  maxLength={MAX_MESSAGE_LENGTH}
                  disabled={Boolean(sending)}
                  style={{ height: '70px' }}
                  aria-label="Message"
                />
                <Button type="submit" disabled={Boolean(sending) || !text.trim()}>
                  {sending ? <Spinner size="sm" label="Sending…" /> : 'Send'}
                </Button>
              </Box>
            </>
          )}
        </CardBody>
      </Card>
    </Box>
  )
}

function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const presentation = message.presentation
  return (
    <Box
      className={cx(
        'sc-chat__bubble',
        isUser ? 'sc-chat__bubble--user' : 'sc-chat__bubble--assistant',
        message.is_error && 'sc-chat__bubble--error',
      )}
    >
      <Box className="sc-chat__text">{message.content}</Box>
      {presentation && (
        <Box className="mt-2">
          <a href={presentation.url} target="_blank" rel="noopener noreferrer">
            Open “{presentation.title}” in Google Slides ↗
          </a>
        </Box>
      )}
      {message.created_at && (
        <Box className="sc-chat__time">
          {new Date(message.created_at).toLocaleTimeString()}
        </Box>
      )}
    </Box>
  )
}
