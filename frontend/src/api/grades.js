import client from './client'

export function listGrades() {
  return client.get('/grades/')
}
