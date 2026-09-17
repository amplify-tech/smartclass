import client from './client'

export function listSubjects() {
  return client.get('/subjects/')
}
