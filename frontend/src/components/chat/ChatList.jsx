import { Box, Button, ErrorPanel, LoadingBlock, cx } from '../common_ui'
import { formatDateTime } from '../../utils/formatDate'

export default function ChatList({
  chats,
  activeChatId,
  status,
  error,
  creating,
  onNewChat,
  onRetry,
  onSelectChat,
}) {
  return (
    <aside className="sc-chat-list">
      <Box className="sc-chat-list__header">
        <Button block onClick={onNewChat} disabled={creating}>
          {creating ? 'Creating…' : '+ New Chat'}
        </Button>
      </Box>

      {status === 'loading' ? (
        <LoadingBlock label="Loading chats…" className="py-4" />
      ) : null}
      {status === 'error' ? (
        <ErrorPanel message={error} onRetry={onRetry} className="px-3" />
      ) : null}
      {status === 'ready' && chats.length === 0 ? (
        <Box className="p-3 small text-muted">No chats yet.</Box>
      ) : null}
      {status === 'ready' ? (
        <Box className="list-group list-group-flush sc-chat-list__items">
          {chats.map((chat) => (
            <button
              key={chat.id}
              type="button"
              className={cx(
                'list-group-item list-group-item-action text-start',
                String(chat.id) === String(activeChatId) && 'active',
              )}
              onClick={() => onSelectChat(chat.id)}
            >
              <span className="d-block text-truncate fw-medium">
                {chat.title || 'New chat'}
              </span>
              <span className="d-block small opacity-75">
                {formatDateTime(chat.updated_at)}
              </span>
            </button>
          ))}
        </Box>
      ) : null}
    </aside>
  )
}
