import client from './client'

/**
 * List questions with optional filters and pagination.
 *
 * Params: page, page_size, search, grade, subject, label,
 *         question_type, difficulty
 */
export function listQuestions(params = {}) {
  return client.get('/questions/', { params })
}

export function getQuestion(id) {
  return client.get(`/questions/${id}/`)
}

export function createQuestion(payload) {
  return client.post('/questions/', payload)
}

export function updateQuestion(id, payload) {
  return client.patch(`/questions/${id}/`, payload)
}

export function deleteQuestion(id) {
  return client.delete(`/questions/${id}/`)
}
