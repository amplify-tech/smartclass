import client from './client'

const MESSAGE_TIMEOUT_MS = 180000

export function listChats(chatType, params = {}) {
  return client.get('/conversations/', {
    params: { ...params, chat_type: chatType },
  })
}

export function getChat(id) {
  return client.get(`/conversations/${id}/`)
}

export function createChat(chatType, context = {}) {
  return client.post('/conversations/', {
    chat_type: chatType,
    context,
  })
}

export function sendChatMessage(id, content) {
  return client.post(
    `/conversations/${id}/messages/`,
    { content },
    { timeout: MESSAGE_TIMEOUT_MS },
  )
}
