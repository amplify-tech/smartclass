import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'

import GuestOnly from './components/auth/GuestOnly'
import RequireAuth from './components/auth/RequireAuth'
import AppLayout from './components/layout/AppLayout'
import { CatalogProvider } from './contexts/CatalogContext'
import AuthPage from './pages/AuthPage'
import CreateExamPage from './pages/CreateExamPage'
import DocumentUploadPage from './pages/DocumentUploadPage'
import DocumentsPage from './pages/DocumentsPage'
import ExamPaperBuilderPage from './pages/ExamPaperBuilderPage'
import ExamPreviewPage from './pages/ExamPreviewPage'
import ExamsPage from './pages/ExamsPage'
import GenerateQuestionsPage from './pages/GenerateQuestionsPage'
import GenerationTaskPage from './pages/GenerationTaskPage'
import HomePage from './pages/HomePage'
import PendingTasksPage from './pages/PendingTasksPage'
import PptsPage from './pages/PptsPage'
import QuestionBankPage from './pages/QuestionBankPage'
import { isAuthenticated } from './utils/authTokens'

function CatchAllRedirect() {
  window.location.replace(isAuthenticated() ? '/' : '/auth')
  return null
}

function LegacyRedirect({ to }) {
  const { search } = useLocation()
  return <Navigate to={`${to}${search}`} replace />
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

            <Route path="/exams" element={<ExamsPage />} />
            <Route path="/exams/question-bank" element={<QuestionBankPage />} />
            <Route path="/exams/generate" element={<GenerateQuestionsPage />} />
            <Route
              path="/generation-tasks/:taskId"
              element={<GenerationTaskPage />}
            />
            <Route path="/exams/pending-tasks" element={<PendingTasksPage />} />
            <Route path="/exams/create" element={<CreateExamPage />} />
            <Route path="/exams/:examId/build" element={<ExamPaperBuilderPage />} />
            <Route path="/exams/:examId/preview" element={<ExamPreviewPage />} />

            {/* Legacy redirects */}
            <Route
              path="/question-bank"
              element={<LegacyRedirect to="/exams/question-bank" />}
            />
            <Route
              path="/create-exam"
              element={<LegacyRedirect to="/exams/create" />}
            />

            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/documents/upload" element={<DocumentUploadPage />} />
            <Route path="/ppts" element={<PptsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<CatchAllRedirect />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
