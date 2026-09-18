import axios from 'axios'

import { getAccessToken } from '../utils/authTokens'
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

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url || ''

    if (status === 401 && !isAuthEndpoint(url)) {
      redirectToAuth()
    }

    return Promise.reject(error)
  },
)

export default client
