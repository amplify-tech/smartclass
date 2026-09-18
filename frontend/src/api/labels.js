import client from './client'

export function listLabels() {
  return client.get('/labels/')
}

export function createLabel(payload) {
  return client.post('/labels/', payload)
}
