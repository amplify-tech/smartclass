import './ExamPrintPreview.css'

const OPTION_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

const DEFAULT_INSTRUCTIONS = [
  'Answer all questions.',
  'Read each question carefully.',
  'Write neatly and clearly.',
]

function sortByOrder(items) {
  return [...items].sort((a, b) => (a.order || 0) - (b.order || 0))
}

function instructionLines(description) {
  const lines = String(description || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
  return lines.length > 0 ? lines : DEFAULT_INSTRUCTIONS
}

function formatDuration(minutes) {
  const value = Number(minutes)
  if (!Number.isFinite(value) || value < 1) return '—'
  return `${value} Minute${value === 1 ? '' : 's'}`
}

function QuestionBlock({ index, placement }) {
  const question = placement.question || {}
  const marks = Number(question.marks) || 0
  const type = question.question_type
  const options = sortByOrder(question.options || [])

  return (
    <li className="exam-print-preview__question">
      <div className="exam-print-preview__question-header">
        <p className="exam-print-preview__question-text">
          Q{index}. {question.text || '—'}
        </p>
        <span className="exam-print-preview__marks">({marks})</span>
      </div>

      {type === 'mcq' && options.length > 0 && (
        <ul className="exam-print-preview__options">
          {options.map((option, optionIndex) => (
            <li key={option.id || optionIndex}>
              {OPTION_LETTERS[optionIndex] || optionIndex + 1}. {option.text}
            </li>
          ))}
        </ul>
      )}
    </li>
  )
}

/**
 * School-exam paper layout for on-screen preview and @media print.
 */
export default function ExamPrintPreview({
  exam,
  gradeName,
  subjectName,
  toolbar,
}) {
  const placements = sortByOrder(exam?.exam_questions || [])
  const instructions = instructionLines(exam?.description)
  const headingParts = [exam?.title, subjectName].filter(Boolean)
  const paperHeading = headingParts.join(' – ').toUpperCase()

  return (
    <div className="exam-print-preview">
      {toolbar ? (
        <div className="exam-print-preview__toolbar d-print-none">
          {toolbar}
        </div>
      ) : null}

      <article className="exam-print-preview__paper">
        <h1 className="exam-print-preview__school">
          {exam?.school_name || 'School'}
        </h1>
        <h2 className="exam-print-preview__title">{paperHeading || 'EXAM'}</h2>

        <div className="exam-print-preview__meta">
          <div className="exam-print-preview__meta-row">
            <span className="exam-print-preview__meta-label">Class:</span>
            <span>{gradeName || '—'}</span>
          </div>
          <div className="exam-print-preview__meta-row">
            <span className="exam-print-preview__meta-label">Time:</span>
            <span>{formatDuration(exam?.duration_minutes)}</span>
          </div>
          <div className="exam-print-preview__meta-row">
            <span className="exam-print-preview__meta-label">Date:</span>
            <span className="exam-print-preview__blank" />
          </div>
          <div className="exam-print-preview__meta-row">
            <span className="exam-print-preview__meta-label">Max Marks:</span>
            <span>{exam?.total_marks ?? 0}</span>
          </div>
        </div>

        <div className="exam-print-preview__student">
          <div className="exam-print-preview__student-row">
            <span className="exam-print-preview__meta-label">Name:</span>
            <span className="exam-print-preview__blank" />
            <span className="exam-print-preview__meta-label">Roll No:</span>
            <span className="exam-print-preview__blank exam-print-preview__blank--roll" />
          </div>
        </div>

        <section className="exam-print-preview__instructions">
          <p className="exam-print-preview__instructions-title">Instructions:</p>
          <ol className="exam-print-preview__instructions-list">
            {instructions.map((line, index) => (
              <li key={`${index}-${line}`}>{line}</li>
            ))}
          </ol>
        </section>

        <hr className="exam-print-preview__rule" />

        {placements.length === 0 ? (
          <p className="exam-print-preview__empty">
            No questions on this paper yet.
          </p>
        ) : (
          <ol className="exam-print-preview__questions">
            {placements.map((placement, index) => (
              <QuestionBlock
                key={placement.id}
                index={index + 1}
                placement={placement}
              />
            ))}
          </ol>
        )}

        <hr className="exam-print-preview__rule" />
      </article>
    </div>
  )
}
