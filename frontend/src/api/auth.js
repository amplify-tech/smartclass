import client from './client'

export function login({ email, password }) {
  return client.post('/auth/token/', { email, password })
}

export function register(payload) {
  return client.post('/auth/register/', payload)
}

export function refreshToken(refresh) {
  return client.post('/auth/token/refresh/', { refresh })
}
