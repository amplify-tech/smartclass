import { createContext, useContext, useEffect, useState } from 'react'

import { getProfile } from '../api/auth'
import { listGrades } from '../api/grades'
import { listSubjects } from '../api/subjects'
import { Alert, Box, Button, Spinner } from '../components/common_ui'

const CatalogContext = createContext(null)

export function CatalogProvider({ children }) {
  const [user, setUser] = useState(null)
  const [grades, setGrades] = useState([])
  const [subjects, setSubjects] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState(null)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function fetchCatalog() {
      setStatus('loading')
      setError(null)

      try {
        const [profileRes, gradesRes, subjectsRes] = await Promise.all([
          getProfile(),
          listGrades(),
          listSubjects(),
        ])

        if (!cancelled) {
          setUser(profileRes.data)
          setGrades(gradesRes.data)
          setSubjects(subjectsRes.data)
          setStatus('ready')
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err.response?.data?.detail ||
            err.response?.data?.error ||
            err.message ||
            'Failed to load app data'
          setError(message)
          setStatus('error')
        }
      }
    }

    fetchCatalog()

    return () => {
      cancelled = true
    }
  }, [reloadToken])

  function reload() {
    setReloadToken((n) => n + 1)
  }

  if (status === 'loading') {
    return <Spinner fullPage label="Loading…" />
  }

  if (status === 'error') {
    return (
      <Box className="min-vh-100 d-flex flex-column align-items-center justify-content-center gap-3 p-4 bg-white">
        <Alert variant="danger">{error}</Alert>
        <Button type="button" onClick={reload}>
          Try again
        </Button>
      </Box>
    )
  }

  return (
    <CatalogContext.Provider value={{ user, grades, subjects, reload }}>
      {children}
    </CatalogContext.Provider>
  )
}

export function useCatalog() {
  const value = useContext(CatalogContext)
  if (!value) {
    throw new Error('useCatalog must be used within a CatalogProvider')
  }
  return value
}
