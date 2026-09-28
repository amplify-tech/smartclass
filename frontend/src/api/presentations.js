import client from './client'

// The LLM + Slides MCP calls run inside this request, so it can take a while.
const MESSAGE_TIMEOUT_MS = 180000

export function listConversations(params = {}) {
  return client.get('/presentation-conversations/', { params })
}

export function getConversation(id) {
  return client.get(`/presentation-conversations/${id}/`)
}

export function createConversation() {
  return client.post('/presentation-conversations/', {})
}

/** Send a teacher message; responds with the whole updated conversation. */
export function sendConversationMessage(id, content) {
  return client.post(
    `/presentation-conversations/${id}/messages/`,
    { content },
    { timeout: MESSAGE_TIMEOUT_MS },
  )
}
