import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import AppLayout from './components/layout/AppLayout'
import { CatalogProvider } from './contexts/CatalogContext'
import AuthPage from './pages/AuthPage'
import DocumentsPage from './pages/DocumentsPage'
import ExamsPage from './pages/ExamsPage'
import HomePage from './pages/HomePage'
import PptsPage from './pages/PptsPage'
import QuestionBankPage from './pages/QuestionBankPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth" element={<AuthPage />} />
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
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
