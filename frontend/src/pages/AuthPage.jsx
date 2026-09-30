import { Link } from 'react-router-dom'

import LoginForm from '../components/auth/LoginForm'
import RegisterForm from '../components/auth/RegisterForm'
import {
  Card,
  CardBody,
  Tab,
  TabContent,
  TabPane,
  Tabs,
} from '../components/common_ui'

import './Home.css'
import './PublicNavbar.css'

export default function AuthPage() {
  return (
    <>
    <header className="sc-navbar">
      <div className="sc-nav-container">
        <Link to="/" className="sc-logo">
          SmartClass
        </Link>

        <nav className="sc-nav-links" aria-label="Main navigation">
          <Link to="/#features">Features</Link>
          <Link to="/#faq">FAQ</Link>
        </nav>

        <div className="sc-nav-actions">
          <Link to="/" className="sc-nav-cta">
            About
          </Link>
        </div>
      </div>
    </header>

    <main className="smartclass-home">
      <section className="sc-hero sc-auth-hero">
        <div className="sc-container sc-hero-grid">
          <div>
            <span className="sc-eyebrow">AI-powered learning & teaching</span>

            <h1>
              Turn your teaching material into{" "}
              <span>ready-to-use learning content.</span>
            </h1>

            <p className="sc-hero-text">
              SmartClass helps teachers create questions, quizzes, exams and
              lecture presentations from their own material and helps
              learners study smarter from the content they already have.
            </p>
          </div>

          <Card className="sc-auth-card">
            <Tabs className="sc-auth-switch">
              <Tab id="login-tab" target="#login-pane" active>
                Login
              </Tab>
              <Tab id="register-tab" target="#register-pane">
                Register
              </Tab>
            </Tabs>

            <CardBody className="p-4">
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
        </div>
      </section>
    </main>
  </>
  )
}
