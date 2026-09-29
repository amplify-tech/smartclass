import { useEffect, useRef } from 'react'

import { Box, EmptyState, Spinner } from '../common_ui'
import ChatMessage from './ChatMessage'

export default function ChatMessageList({
  messages,
  pendingMessage,
  emptyTitle,
  emptyDescription,
}) {
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, pendingMessage])

  return (
    <Box className="sc-chat__messages">
      {messages.length === 0 && !pendingMessage ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : null}

      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}

      {pendingMessage ? (
        <>
          <ChatMessage message={{ role: 'user', content: pendingMessage }} />
          <Box className="sc-chat__bubble sc-chat__bubble--assistant d-flex align-items-center gap-2">
            <Spinner size="sm" label="Working…" />
            <span className="text-muted">Working on it…</span>
          </Box>
        </>
      ) : null}
      <div ref={endRef} />
    </Box>
  )
}
