import client from './client'

export function listPresentations(params = {}) {
  return client.get('/presentations/', { params })
}
