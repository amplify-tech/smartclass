import { Link } from "react-router-dom";

import "./Home.css";
import "./PublicNavbar.css";

export default function Home() {
  return (
    <>
    <header className="sc-navbar">
      <div className="sc-nav-container">
        <Link to="/" className="sc-logo">
          SmartClass
        </Link>

        <nav className="sc-nav-links" aria-label="Main navigation">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>
          <a href="#about">About</a>
          <a href="#faq">FAQ</a>
        </nav>

        <div className="sc-nav-actions">
          <Link to="/login" className="sc-login-link">
            Log in
          </Link>

          <Link to="/login" className="sc-nav-cta">
            Get started
          </Link>
        </div>
      </div>
    </header>
    <main className="smartclass-home">

      {/* HERO */}
      <section className="sc-hero">
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

            <div className="sc-actions">
              <Link to="/login" className="sc-btn sc-btn-primary">
                Get Started
              </Link>

              <a href="#how-it-works" className="sc-btn sc-btn-secondary">
                See How It Works
              </a>
            </div>
          </div>

          <div className="sc-product-preview" aria-label="SmartClass product preview">
            <div className="sc-window">
              <div className="sc-window-top">
                <span className="sc-dot" />
                <span className="sc-dot" />
                <span className="sc-dot" />
              </div>

              <div className="sc-preview-body">
                <aside className="sc-sidebar">
                  <div className="sc-side-line" />
                  <div className="sc-side-line" />
                  <div className="sc-side-line" />
                  <div className="sc-side-line" />
                </aside>

                <div className="sc-main-preview">
                  <div className="sc-preview-title" />

                  <div className="sc-flow">
                    <div className="sc-flow-card">
                      <strong>📄 Your Material</strong>
                      <p>Grade 8 · Science · Photosynthesis</p>
                    </div>

                    <div className="sc-flow-arrow">↓</div>

                    <div className="sc-flow-card">
                      <strong>✨ SmartClass AI</strong>
                      <p>
                        Generate questions using your material and instructions.
                      </p>
                    </div>

                    <div className="sc-flow-arrow">↓</div>

                    <div className="sc-flow-card">
                      <strong>✓ Ready to Review</strong>
                      <p>
                        Questions · Quiz · Exam · Learning material
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PROBLEM */}
      <section className="sc-section sc-problem">
        <div className="sc-container">
          <div className="sc-centered">
            <span className="sc-eyebrow">The problem</span>
            <h2>Creating learning material shouldn't take hours.</h2>
            <p>
              Teachers and learners already have valuable material. The hard
              part is turning that material into useful questions, assessments
              and learning content.
            </p>
          </div>

          <div className="sc-problem-grid">
            <article className="sc-card">
              <span className="sc-card-number">01</span>
              <h3>Too much manual work</h3>
              <p>
                Creating questions, quizzes and exam papers manually can take
                hours.
              </p>
            </article>

            <article className="sc-card">
              <span className="sc-card-number">02</span>
              <h3>Keeping content relevant</h3>
              <p>
                Questions should be based on the material actually being taught
                or studied.
              </p>
            </article>

            <article className="sc-card">
              <span className="sc-card-number">03</span>
              <h3>Scattered workflows</h3>
              <p>
                Creating, reviewing, organizing and using questions often
                happens across different tools.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* SOLUTION */}
      <section className="sc-section" id="features">
        <div className="sc-container">
          <div className="sc-centered" >
            <span className="sc-eyebrow">The solution</span>
            <h2>One place to create, organize and learn.</h2>
            <p>
              Bring your teaching or study material into SmartClass and use AI
              to turn it into useful educational content.
            </p>
          </div>

          <div className="sc-features">
            <article className="sc-feature">
              <div className="sc-icon">Q</div>
              <h3>Generate questions with AI</h3>
              <p>
                Create educational questions from your material and
                instructions in seconds.
              </p>
            </article>

            <article className="sc-feature">
              <div className="sc-icon">E</div>
              <h3>Create exams faster</h3>
              <p>
                Turn selected questions into a ready-to-use exam paper in
                seconds.
              </p>
            </article>

            <article className="sc-feature">
              <div className="sc-icon">P</div>
              <h3>Create lecture presentations</h3>
              <p>
                Turn lecture material into a ready-to-use PPT for teaching.
              </p>
            </article>

            <article className="sc-feature">
              <div className="sc-icon">B</div>
              <h3>Build your question bank</h3>
              <p>
                Review, organize and reuse generated questions whenever you
                need them.
              </p>
            </article>

            <article className="sc-feature">
              <div className="sc-icon">L</div>
              <h3>Learn from your material</h3>
              <p>
                Explore and revise your own study material with AI-assisted
                learning.
              </p>
            </article>

            <article className="sc-feature">
              <div className="sc-icon">R</div>
              <h3>Grounded in your content</h3>
              <p>
                Relevant content from your documents can provide context for
                AI-generated learning content.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="sc-section sc-problem">
        <div className="sc-container">
          <div className="sc-centered">
            <span className="sc-eyebrow">How it works</span>
            <h2>From material to learning content.</h2>
            <p>
              A simple workflow designed around the material you already use.
            </p>
          </div>

          <div className="sc-steps">
            <article className="sc-step">
              <span className="sc-step-number">01</span>
              <h3>Upload</h3>
              <p>Add your teaching or study material.</p>
            </article>

            <article className="sc-step">
              <span className="sc-step-number">02</span>
              <h3>Instruct</h3>
              <p>Tell SmartClass what you want to create.</p>
            </article>

            <article className="sc-step">
              <span className="sc-step-number">03</span>
              <h3>Generate</h3>
              <p>Create questions, exams, presentations or learning content.</p>
            </article>

            <article className="sc-step">
              <span className="sc-step-number">04</span>
              <h3>Review</h3>
              <p>Review and refine the generated content.</p>
            </article>

            <article className="sc-step">
              <span className="sc-step-number">05</span>
              <h3>Use</h3>
              <p>Teach, practice, revise or create your exam.</p>
            </article>
          </div>
        </div>
      </section>

      {/* SCREENSHOTS */}
      <section className="sc-section sc-showcase">
        <div className="sc-container">
          <div className="sc-centered">
            <span className="sc-eyebrow">Inside SmartClass</span>
            <h2>See SmartClass in action.</h2>
            <p>
              A simple workspace for turning your educational material into
              useful content.
            </p>
          </div>

          <div className="sc-screenshots">
            <figure className="sc-screenshot">
              <img
                src="/screenshots/home1.png"
                alt="SmartClass AI question generator"
                loading="lazy"
              />
              <figcaption className="sc-screenshot-caption">
                <strong>AI Question Generation</strong>
                <span>Create questions from your teaching material.</span>
              </figcaption>
            </figure>

            <figure className="sc-screenshot">
              <img
                src="/screenshots/home2.png"
                alt="SmartClass question bank"
                loading="lazy"
              />
              <figcaption className="sc-screenshot-caption">
                <strong>Question Bank</strong>
                <span>Review and organize your generated questions.</span>
              </figcaption>
            </figure>

            <figure className="sc-screenshot">
              <img
                src="/screenshots/home3.png"
                alt="SmartClass exam paper builder"
                loading="lazy"
              />
              <figcaption className="sc-screenshot-caption">
                <strong>Exam Paper Builder</strong>
                <span>Turn selected questions into an exam.</span>
              </figcaption>
            </figure>

            <figure className="sc-screenshot">
              <img
                src="/screenshots/home4.png"
                alt="SmartClass presentation generation"
                loading="lazy"
              />
              <figcaption className="sc-screenshot-caption">
                <strong>Lecture Presentations</strong>
                <span>Create ready-to-use presentation content.</span>
              </figcaption>
            </figure>
          </div>
        </div>
      </section>

      {/* AUDIENCE */}
      <section className="sc-section">
        <div className="sc-container">
          <div className="sc-centered">
            <span className="sc-eyebrow">Who it's for</span>
            <h2>Built for teaching and learning.</h2>
          </div>

          <div className="sc-audience">
            <article>
              <h3>Teachers</h3>
              <p>
                Create questions, quizzes, exams and lecture material faster
                from the content you already teach.
              </p>
            </article>

            <article>
              <h3>Educators</h3>
              <p>
                Turn existing educational material into structured and
                reusable learning content.
              </p>
            </article>

            <article>
              <h3>Learners</h3>
              <p>
                Study and revise from your own learning material with
                AI-assisted support.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* ABOUT */}
      <section className="sc-section sc-problem" id="about">
        <div className="sc-container sc-about">
          <h2>Built around the material you already have.</h2>

          <div>
            <p>
              SmartClass is an educational platform designed to make content
              creation and learning simpler.
            </p>

            <p>
              Instead of starting from scratch, teachers and learners can bring
              their own material into SmartClass and use AI to create,
              organize, review and learn from it.
            </p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="sc-section" id="faq">
        <div className="sc-container">
          <div className="sc-centered">
            <span className="sc-eyebrow">FAQ</span>
            <h2>Questions about SmartClass?</h2>
          </div>

          <div className="sc-faq">
            <details>
              <summary>What is SmartClass?</summary>
              <p>
                SmartClass is an AI-powered education platform that helps
                teachers and learners create and work with educational content
                using their own material.
              </p>
            </details>

            <details>
              <summary>Can SmartClass generate questions from documents?</summary>
              <p>
                Yes. SmartClass can use relevant content from uploaded documents
                as context when generating educational questions.
              </p>
            </details>

            <details>
              <summary>Can I create an exam with SmartClass?</summary>
              <p>
                Yes. Questions can be reviewed and organized in the question
                bank and used to create exam papers.
              </p>
            </details>

            <details>
              <summary>Can SmartClass create lecture presentations?</summary>
              <p>
                SmartClass can help turn lecture material into presentation
                content that can be used for teaching.
              </p>
            </details>

            <details>
              <summary>Can learners use their own study material?</summary>
              <p>
                Yes. SmartClass is designed to help learners explore and revise
                their own study material with AI-assisted learning.
              </p>
            </details>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="sc-cta">
        <div className="sc-container">
          <h2>Create more. Prepare faster. Learn smarter.</h2>

          <p>
            Bring your teaching or study material into SmartClass and turn it
            into useful learning content with AI.
          </p>

          <div className="sc-actions">
            <Link to="/login" className="sc-btn sc-btn-primary">
              Get Started
            </Link>
          </div>
        </div>
      </section>
    </main>

    {/* FOOTER */}
    <footer className="sc-footer">
      <div className="sc-container sc-footer-inner">
        <div>
          <strong>SmartClass</strong>
          <div>AI-powered tools for teaching and learning.</div>
        </div>

        <div>© {new Date().getFullYear()} SmartClass</div>
      </div>
    </footer>
  </>
  );
}