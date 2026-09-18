import { BrowserRouter, Route, Routes } from 'react-router-dom'

import GuestOnly from './components/auth/GuestOnly'
import RequireAuth from './components/auth/RequireAuth'
import AppLayout from './components/layout/AppLayout'
import { CatalogProvider } from './contexts/CatalogContext'
import AuthPage from './pages/AuthPage'
import DocumentsPage from './pages/DocumentsPage'
import ExamsPage from './pages/ExamsPage'
import HomePage from './pages/HomePage'
import PptsPage from './pages/PptsPage'
import QuestionBankPage from './pages/QuestionBankPage'
import { isAuthenticated } from './utils/authTokens'

function CatchAllRedirect() {
  window.location.replace(isAuthenticated() ? '/' : '/auth')
  return null
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<GuestOnly />}>
          <Route path="/auth" element={<AuthPage />} />
        </Route>

        <Route element={<RequireAuth />}>
          <Route
            element={
              <CatalogProvider>
                <AppLayout />
              </CatalogProvider>
            }
          >
            <Route path="/" element={<HomePage />} />
            <Route path="/question-bank" element={<QuestionBankPage />} />
            <Route path="/exams" element={<ExamsPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/ppts" element={<PptsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<CatchAllRedirect />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
