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

/**
 * Reorder questions on an exam.
 * @param {number|string} examId
 * @param {{ items: { exam_question_id: number, order: number }[] }} payload
 */
export function reorderExamQuestions(examId, payload) {
  return client.put(`/exams/${examId}/reorder-questions/`, payload)
}

/**
 * Remove a placed question from an exam.
 * @param {number|string} examId
 * @param {number|string} examQuestionId
 */
export function removeExamQuestion(examId, examQuestionId) {
  return client.delete(`/exams/${examId}/exam-questions/${examQuestionId}/`)
}

/**
 * Update a placed question (order and/or marks).
 * @param {number|string} examId
 * @param {number|string} examQuestionId
 * @param {{ order?: number, marks?: number }} payload
 */
export function updateExamQuestion(examId, examQuestionId, payload) {
  return client.patch(
    `/exams/${examId}/exam-questions/${examQuestionId}/`,
    payload,
  )
}
