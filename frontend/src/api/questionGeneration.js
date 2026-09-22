import client from './client'

export function listQuestionGenerationJobs(params = {}) {
  return client.get('/question-generation-jobs/', { params })
}

export function createQuestionGenerationJob(payload) {
  return client.post('/question-generation-jobs/', payload)
}

export function getQuestionGenerationJob(jobId) {
  return client.get(`/question-generation-jobs/${jobId}/`)
}

export function getLatestQuestionGenerationJob() {
  return client.get('/question-generation-jobs/latest/')
}

/** Current user's most recent job id. */
export async function getLatestQuestionGenerationJobId() {
  const { data } = await getLatestQuestionGenerationJob()
  return data?.id ?? null
}
