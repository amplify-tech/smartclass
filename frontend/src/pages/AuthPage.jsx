import LoginForm from '../components/auth/LoginForm'
import RegisterForm from '../components/auth/RegisterForm'
import {
  Box,
  Card,
  CardBody,
  Tab,
  TabContent,
  TabPane,
  Tabs,
} from '../components/common_ui'
import { isAuthenticated } from '../utils/authTokens'

export default function AuthPage() {
  if (isAuthenticated()) {
    window.location.replace('/')
    return null
  }

  return (
    <Box className="container py-5">
      <Box className="row justify-content-center">
        <Box className="col-md-6 col-lg-5">
          <Box className="text-center mb-4">
            <h1 className="h3 mb-1">SmartClass</h1>
            <p className="text-muted mb-0">Sign in or create an account</p>
          </Box>

          <Card className="shadow-sm">
            <CardBody className="p-4">
              <Tabs className="mb-4">
                <Tab id="login-tab" target="#login-pane" active>
                  Login
                </Tab>
                <Tab id="register-tab" target="#register-pane">
                  Register
                </Tab>
              </Tabs>

              <TabContent>
                <TabPane id="login-pane" labelledBy="login-tab" active>
                  <LoginForm />
                </TabPane>
                <TabPane id="register-pane" labelledBy="register-tab">
                  <RegisterForm />
                </TabPane>
              </TabContent>
            </CardBody>
          </Card>
        </Box>
      </Box>
    </Box>
  )
}
