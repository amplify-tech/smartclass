import client from './client'

export function listDocuments() {
  return client.get('/documents/')
}

/**
 * Upload a document (multipart). Pass a FormData with title, file, doc_type,
 * grade, and subject. Content-Type is left unset so the browser sets the boundary.
 */
export function createDocument(formData) {
  return client.post('/documents/', formData, {
    headers: { 'Content-Type': undefined },
  })
}
