import client from './client'

export function listDocuments() {
  return client.get('/documents/')
}
