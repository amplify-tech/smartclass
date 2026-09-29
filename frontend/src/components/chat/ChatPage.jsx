import { useNavigate } from 'react-router-dom'

import {
  Alert,
  Box,
  Card,
  ErrorPanel,
  LoadingBlock,
  PageHeader,
} from '../common_ui'
import ChatComposer from './ChatComposer'
import ChatList from './ChatList'
import ChatMessageList from './ChatMessageList'
import useChatSession from './useChatSession'

export default function ChatPage({
  chatType,
  chatId,
  chatPath,
  breadcrumbs,
  description,
  emptyTitle = 'Start a new chat',
  emptyDescription,
  context = {},
}) {
  const navigate = useNavigate()
  const {
    chats,
    listStatus,
    listError,
    creating,
    create,
    retryList,
    conversation,
    chatStatus,
    chatError,
    retryChat,
    text,
    setText,
    pendingMessage,
    sendError,
    send,
  } = useChatSession(chatType, chatId)

  async function createNewChat() {
    const created = await create(context)
    if (created) navigate(chatPath(created.id))
  }

  const title = conversation?.title || 'Chat'

  return (
    <Box>
      <PageHeader
        breadcrumbs={[...breadcrumbs, { label: title }]}
        title={title}
        description={description}
      />

      <Card className="sc-chat-layout">
        <ChatList
          chats={chats}
          activeChatId={chatId}
          status={listStatus}
          error={listError}
          creating={creating}
          onNewChat={createNewChat}
          onRetry={retryList}
          onSelectChat={(id) => navigate(chatPath(id))}
        />

        <Box className="sc-chat-window">
          {chatStatus === 'loading' ? <LoadingBlock label="Loading chat…" /> : null}
          {chatStatus === 'error' ? (
            <ErrorPanel message={chatError} onRetry={retryChat} />
          ) : null}
          {chatStatus === 'ready' && conversation ? (
            <>
              <ChatMessageList
                messages={conversation.messages || []}
                pendingMessage={pendingMessage}
                emptyTitle={emptyTitle}
                emptyDescription={emptyDescription}
              />
              {sendError ? (
                <Alert variant="danger" className="mb-2">
                  {sendError}
                </Alert>
              ) : null}
              <ChatComposer
                value={text}
                onChange={setText}
                onSend={send}
                sending={Boolean(pendingMessage)}
              />
            </>
          ) : null}
        </Box>
      </Card>
    </Box>
  )
}
