import { useEffect, useState } from 'react'

import {
  getJobStatus,
  getQuestionGenerationJob,
} from '../api/questionGeneration'
import { getApiErrorMessage } from '../utils/apiErrors'

const JOB_POLL_INTERVAL_MS = 2000
const ACTIVE_STATUSES = new Set(['pending', 'running', 'loading'])

function isMatchingJob(jobId, job) {
  return job != null && jobId != null && String(job.id) === String(jobId)
}

export default function useQuestionGenerationJob(jobId, initialJob = null) {
  const seededJob = isMatchingJob(jobId, initialJob) ? initialJob : null

  const [job, setJob] = useState(seededJob)
  const [status, setStatus] = useState(() => {
    if (!jobId) return 'idle'
    if (seededJob?.status) return seededJob.status
    return 'loading'
  })
  const [error, setError] = useState(() =>
    seededJob?.status === 'failed'
      ? seededJob.error_message || 'Question generation failed'
      : null,
  )

  useEffect(() => {
    if (!jobId) {
      setJob(null)
      setStatus('idle')
      setError(null)
      return undefined
    }

    let cancelled = false
    let timerId

    if (!isMatchingJob(jobId, job)) {
      setJob(null)
      setStatus('loading')
      setError(null)
    }

    async function loadDetails() {
      const { data } = await getQuestionGenerationJob(jobId)
      if (cancelled) return null
      setJob(data)
      setStatus(data.status)
      setError(
        data.status === 'failed'
          ? data.error_message || 'Question generation failed'
          : null,
      )
      return data.status
    }

    async function poll() {
      try {
        const { data } = await getJobStatus(jobId)
        if (cancelled) return

        if (data.status === 'pending' || data.status === 'running') {
          timerId = setTimeout(poll, JOB_POLL_INTERVAL_MS)
          return
        }

        await loadDetails()
      } catch (err) {
        if (cancelled) return
        setStatus('error')
        setJob(null)
        setError(getApiErrorMessage(err, 'Failed to check generation status'))
      }
    }

    ;(async () => {
      try {
        const appStatus = await loadDetails()
        if (cancelled) return
        if (appStatus === 'pending' || appStatus === 'running') poll()
      } catch (err) {
        if (cancelled) return
        setStatus('error')
        setJob(null)
        setError(getApiErrorMessage(err, 'Failed to check generation status'))
      }
    })()

    return () => {
      cancelled = true
      clearTimeout(timerId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- poll only when jobId changes
  }, [jobId])

  return {
    job,
    status,
    error,
    isPolling: ACTIVE_STATUSES.has(status),
    questionCount: Array.isArray(job?.question_ids) ? job.question_ids.length : 0,
  }
}
