import client from './client'

/**
 * List documents with optional filters and pagination.
 *
 * Params: page, page_size, search, grade, subject, doc_type, status, ordering
 */
export function listDocuments(params = {}) {
  return client.get('/documents/', { params })
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
