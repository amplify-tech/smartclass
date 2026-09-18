import client from './client'

export function listExams(params = {}) {
  return client.get('/exams/', { params })
}

export function getExam(id) {
  return client.get(`/exams/${id}/`)
}

export function createExam(payload) {
  return client.post('/exams/', payload)
}

export function updateExam(id, payload) {
  return client.patch(`/exams/${id}/`, payload)
}

export function deleteExam(id) {
  return client.delete(`/exams/${id}/`)
}

/**
 * Add bank questions to an exam.
 * @param {number|string} examId
 * @param {{ question_ids: number[] }} payload
 */
export function addExamQuestions(examId, payload) {
  return client.post(`/exams/${examId}/questions/`, payload)
}
