import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  createChat,
  getChat,
  listChats,
  sendChatMessage,
} from '../../api/chat'
import { getApiErrorMessage } from '../../utils/apiErrors'
import { parsePaginatedResponse } from '../../utils/pagination'
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

export default function ChatPage({
  chatType,
  chatId,
  chatPath,
  breadcrumbs,
  description,
  emptyTitle = 'Start a new chat',
  emptyDescription,
}) {
  const navigate = useNavigate()
  const [chats, setChats] = useState([])
  const [listStatus, setListStatus] = useState('loading')
  const [listError, setListError] = useState(null)
  const [listReloadKey, setListReloadKey] = useState(0)
  const [creating, setCreating] = useState(false)

  const [conversation, setConversation] = useState(null)
  const [chatStatus, setChatStatus] = useState('loading')
  const [chatError, setChatError] = useState(null)
  const [chatReloadKey, setChatReloadKey] = useState(0)
  const [text, setText] = useState('')
  const [pendingMessage, setPendingMessage] = useState(null)
  const [sendError, setSendError] = useState(null)

  useEffect(() => {
    let cancelled = false
    listChats(chatType, { page_size: 100 })
      .then(({ data }) => {
        if (cancelled) return
        setChats(parsePaginatedResponse(data).results)
        setListStatus('ready')
      })
      .catch((error) => {
        if (cancelled) return
        setListError(getApiErrorMessage(error, 'Failed to load chats'))
        setListStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [chatType, listReloadKey])

  useEffect(() => {
    let cancelled = false
    getChat(chatId)
      .then(({ data }) => {
        if (cancelled) return
        setConversation(data)
        setChatError(null)
        setChatStatus('ready')
      })
      .catch((error) => {
        if (cancelled) return
        setChatError(getApiErrorMessage(error, 'Failed to load chat'))
        setChatStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [chatId, chatReloadKey])

  async function createNewChat() {
    if (creating) return
    setCreating(true)
    setListError(null)
    try {
      const { data } = await createChat(chatType)
      setListReloadKey((value) => value + 1)
      setChatStatus('loading')
      navigate(chatPath(data.id))
    } catch (error) {
      setListError(getApiErrorMessage(error, 'Failed to create chat'))
      setListStatus('error')
    } finally {
      setCreating(false)
    }
  }

  async function send() {
    const content = text.trim()
    if (!content || pendingMessage || !conversation) return

    setPendingMessage(content)
    setSendError(null)
    setText('')
    try {
      const { data } = await sendChatMessage(conversation.id, content)
      setConversation(data)
      setListReloadKey((value) => value + 1)
    } catch (error) {
      setText(content)
      setSendError(getApiErrorMessage(error, 'Failed to send message'))
    } finally {
      setPendingMessage(null)
    }
  }

  const activeConversation =
    String(conversation?.id) === String(chatId) ? conversation : null
  const title = activeConversation?.title || 'Chat'
  const pageBreadcrumbs = [
    ...breadcrumbs,
    { label: title },
  ]

  return (
    <Box>
      <PageHeader
        breadcrumbs={pageBreadcrumbs}
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
          onRetry={() => {
            setListStatus('loading')
            setListError(null)
            setListReloadKey((value) => value + 1)
          }}
          onSelectChat={(id) => {
            setChatStatus('loading')
            navigate(chatPath(id))
          }}
        />

        <Box className="sc-chat-window">
          {chatStatus === 'loading' ||
          (chatStatus !== 'error' && !activeConversation) ? (
            <LoadingBlock label="Loading chat…" />
          ) : null}
          {chatStatus === 'error' ? (
            <ErrorPanel
              message={chatError}
              onRetry={() => {
                setChatStatus('loading')
                setChatReloadKey((value) => value + 1)
              }}
            />
          ) : null}
          {chatStatus === 'ready' && activeConversation ? (
            <>
              <ChatMessageList
                messages={activeConversation.messages || []}
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
