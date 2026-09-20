import { useEffect, useState } from 'react'

import { getQuestionGenerationJob } from '../api/questionGeneration'

const JOB_POLL_INTERVAL_MS = 2000

const ACTIVE_STATUSES = new Set(['pending', 'running', 'loading'])

function isMatchingJob(jobId, job) {
  return job != null && jobId != null && String(job.id) === String(jobId)
}

/**
 * Poll a question-generation job until it completes or fails.
 * Cleans up the timer on unmount / jobId change. No duplicate intervals.
 *
 * @param {string|number|null|undefined} jobId
 * @param {object|null|undefined} initialJob Optional job payload from navigate state
 */
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

    // Keep seeded job for first paint; don't reset to blank "loading".
    if (!isMatchingJob(jobId, job)) {
      setJob(null)
      setStatus('loading')
      setError(null)
    }

    async function poll() {
      try {
        const { data } = await getQuestionGenerationJob(jobId)
        if (cancelled) return

        setJob(data)
        setStatus(data.status)
        setError(
          data.status === 'failed'
            ? data.error_message || 'Question generation failed'
            : null,
        )

        if (data.status === 'completed' || data.status === 'failed') {
          return
        }

        timerId = setTimeout(poll, JOB_POLL_INTERVAL_MS)
      } catch (err) {
        if (cancelled) return
        setStatus('error')
        setJob(null)
        setError(
          err.response?.data?.detail ||
            err.response?.data?.error ||
            err.message ||
            'Failed to check generation status',
        )
      }
    }

    poll()

    return () => {
      cancelled = true
      clearTimeout(timerId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- poll only when jobId changes
  }, [jobId])

  const isPolling = ACTIVE_STATUSES.has(status)

  return {
    job,
    status,
    error,
    isPolling,
    questionCount: Array.isArray(job?.question_ids) ? job.question_ids.length : 0,
  }
}
