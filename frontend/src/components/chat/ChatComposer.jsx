import { Box, Button, Spinner, Textarea } from '../common_ui'

const MAX_MESSAGE_LENGTH = 4000

export default function ChatComposer({ value, onChange, onSend, sending }) {
  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      onSend()
    }
  }

  return (
    <Box
      as="form"
      className="sc-chat__composer"
      onSubmit={(event) => {
        event.preventDefault()
        onSend()
      }}
    >
      <Textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message… (Enter to send, Shift+Enter for a new line)"
        maxLength={MAX_MESSAGE_LENGTH}
        disabled={sending}
        style={{ height: '70px' }}
        aria-label="Message"
      />
      <Button type="submit" disabled={sending || !value.trim()}>
        {sending ? <Spinner size="sm" label="Sending…" /> : 'Send'}
      </Button>
    </Box>
  )
}
