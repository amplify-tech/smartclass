import { useEffect, useState } from 'react'

import {
  createChat,
  getChat,
  listChats,
  sendChatMessage,
} from '../../api/chat'
import { getApiErrorMessage } from '../../utils/apiErrors'
import { parsePaginatedResponse } from '../../utils/pagination'

export default function useChatSession(chatType, chatId) {
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
  const [seenChatId, setSeenChatId] = useState(chatId)

  // Clear the open chat in the same render the route id changes.
  if (seenChatId !== chatId) {
    setSeenChatId(chatId)
    setConversation(null)
    setChatStatus('loading')
    setChatError(null)
  }

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

  async function create(context = {}) {
    if (creating) return null
    setCreating(true)
    setListError(null)
    try {
      const { data } = await createChat(chatType, context)
      setListReloadKey((value) => value + 1)
      return data
    } catch (error) {
      setListError(getApiErrorMessage(error, 'Failed to create chat'))
      setListStatus('error')
      return null
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

  function retryList() {
    setListStatus('loading')
    setListError(null)
    setListReloadKey((value) => value + 1)
  }

  function retryChat() {
    setChatStatus('loading')
    setChatError(null)
    setChatReloadKey((value) => value + 1)
  }

  return {
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
  }
}
