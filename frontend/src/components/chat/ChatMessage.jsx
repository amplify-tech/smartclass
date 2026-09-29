import { Box, Button, cx } from '../common_ui'

function MessageText({ children }) {
  const parts = String(children || '').split(/(https?:\/\/[^\s]+)/g)
  return parts.map((part, index) =>
    part.startsWith('http://') || part.startsWith('https://') ? (
      <a key={`${part}-${index}`} href={part} target="_blank" rel="noopener noreferrer">
        {part}
      </a>
    ) : (
      part
    ),
  )
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const actions = message.actions || (message.action ? [message.action] : [])

  return (
    <Box
      className={cx(
        'sc-chat__bubble',
        isUser ? 'sc-chat__bubble--user' : 'sc-chat__bubble--assistant',
        message.is_error && 'sc-chat__bubble--error',
      )}
    >
      <Box className="sc-chat__text">
        <MessageText>{message.content}</MessageText>
      </Box>
      {actions.map((action, index) =>
        action.type === 'open_url' && action.url ? (
          <Button
            key={`${action.url}-${index}`}
            as="a"
            href={action.url}
            target="_blank"
            rel="noopener noreferrer"
            size="sm"
            variant="outline"
            className="mt-2"
          >
            {action.label || 'Open'}
          </Button>
        ) : null,
      )}
      {message.created_at ? (
        <Box className="sc-chat__time">
          {new Date(message.created_at).toLocaleTimeString()}
        </Box>
      ) : null}
    </Box>
  )
}
