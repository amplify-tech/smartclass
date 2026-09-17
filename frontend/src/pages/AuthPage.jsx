import { Navigate } from 'react-router-dom'

import LoginForm from '../components/auth/LoginForm'
import RegisterForm from '../components/auth/RegisterForm'
import { Box } from '../components/common_ui'
import { useAuth } from '../context/AuthContext'

export default function AuthPage() {
  const { isAuthenticated } = useAuth()

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return (
    <Box className="container py-5">
      <Box className="row justify-content-center">
        <Box className="col-md-6 col-lg-5">
          <Box className="text-center mb-4">
            <h1 className="h3 mb-1">SmartClass</h1>
            <p className="text-muted mb-0">Sign in or create an account</p>
          </Box>

          <Box className="card shadow-sm">
            <Box className="card-body p-4">
              <ul className="nav nav-tabs mb-4" role="tablist">
                <li className="nav-item" role="presentation">
                  <button
                    className="nav-link active"
                    id="login-tab"
                    data-bs-toggle="tab"
                    data-bs-target="#login-pane"
                    type="button"
                    role="tab"
                    aria-controls="login-pane"
                    aria-selected="true"
                  >
                    Login
                  </button>
                </li>
                <li className="nav-item" role="presentation">
                  <button
                    className="nav-link"
                    id="register-tab"
                    data-bs-toggle="tab"
                    data-bs-target="#register-pane"
                    type="button"
                    role="tab"
                    aria-controls="register-pane"
                    aria-selected="false"
                  >
                    Register
                  </button>
                </li>
              </ul>

              <Box className="tab-content">
                <Box
                  className="tab-pane fade show active"
                  id="login-pane"
                  role="tabpanel"
                  aria-labelledby="login-tab"
                  tabIndex={0}
                >
                  <LoginForm />
                </Box>
                <Box
                  className="tab-pane fade"
                  id="register-pane"
                  role="tabpanel"
                  aria-labelledby="register-tab"
                  tabIndex={0}
                >
                  <RegisterForm />
                </Box>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  )
}
