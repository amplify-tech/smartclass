import { createContext, useContext, useEffect, useState } from 'react'

import { listGrades } from '../api/grades'
import { listSubjects } from '../api/subjects'
import { Alert, Box, Button, Spinner } from '../components/common_ui'
import { isAuthenticated } from '../utils/authTokens'

const CatalogContext = createContext(null)

export function CatalogProvider({ children }) {
  const [grades, setGrades] = useState([])
  const [subjects, setSubjects] = useState([])
  const [status, setStatus] = useState(() =>
    isAuthenticated() ? 'loading' : 'ready',
  )
  const [error, setError] = useState(null)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function fetchCatalog() {
      if (!isAuthenticated()) {
        if (!cancelled) {
          setGrades([])
          setSubjects([])
          setStatus('ready')
          setError(null)
        }
        return
      }

      setStatus('loading')
      setError(null)

      try {
        const [gradesRes, subjectsRes] = await Promise.all([
          listGrades(),
          listSubjects(),
        ])

        if (!cancelled) {
          setGrades(gradesRes.data)
          setSubjects(subjectsRes.data)
          setStatus('ready')
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err.response?.data?.error ||
            err.message ||
            'Failed to load classes and subjects'
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
    return <Spinner fullPage label="Loading classes and subjects…" />
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
    <CatalogContext.Provider value={{ grades, subjects, reload }}>
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
