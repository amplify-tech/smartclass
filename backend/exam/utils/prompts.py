import json


SYSTEM_PROMPT = """You are an exam question generator for school teachers.
Return ONLY valid JSON (no markdown):
{
  "questions": [
    {
      "question_type": "mcq" | "short" | "long",
      "text": "question text",
      "marks": 1,
      "difficulty": "easy" | "medium" | "hard",
      "correct_answer": "answer text",
      "options": [{"text": "choice", "is_correct": true, "order": 1}]
    }
  ]
}
Rules:
- mcq: exactly 4 options, one correct
- short/long: no options, put answer in correct_answer
- follow the requested type counts and total marks
"""


def build_user_prompt(job) -> str:
    type_counts = job.question_types if isinstance(job.question_types, dict) else {}
    total = sum(type_counts.values()) if type_counts else 0
    return (
        f'Grade: {job.grade.name}\n'
        f'Subject: {job.subject.name}\n'
        f'Difficulty: {job.difficulty}\n'
        f'Total marks: {job.total_marks}\n'
        f'Question types: {json.dumps(type_counts)}\n'
        f'Teacher instruction: {job.description or "(none)"}\n'
        f'Generate exactly {total} questions.'
    )
