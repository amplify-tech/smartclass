import axios from 'axios'

import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from '../utils/authTokens'
import { redirectToAuth } from '../utils/authRedirect'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function isAuthEndpoint(url = '') {
  return (
    url.includes('/auth/token/') ||
    url.includes('/auth/token/refresh/') ||
    url.includes('/auth/register/')
  )
}

let refreshPromise = null

async function refreshAccessToken() {
  const refresh = getRefreshToken()
  if (!refresh) {
    throw new Error('No refresh token')
  }

  const { data } = await axios.post(
    `${client.defaults.baseURL}/auth/token/refresh/`,
    { refresh },
    { headers: { 'Content-Type': 'application/json' } },
  )

  if (!data?.access) {
    throw new Error('Refresh response missing access token')
  }

  setTokens({ access: data.access, refresh: data.refresh || refresh })
  return data.access
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status
    const original = error.config
    const url = original?.url || ''

    if (status !== 401 || isAuthEndpoint(url) || !original || original._retry) {
      if (status === 401 && !isAuthEndpoint(url)) {
        redirectToAuth()
      }
      return Promise.reject(error)
    }

    original._retry = true

    try {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }
      const access = await refreshPromise
      original.headers = original.headers || {}
      original.headers.Authorization = `Bearer ${access}`
      return client(original)
    } catch {
      clearTokens()
      redirectToAuth()
      return Promise.reject(error)
    }
  },
)

export default client
