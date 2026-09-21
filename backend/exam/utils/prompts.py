import json


SYSTEM_PROMPT = """You are an expert school exam question generator.

Generate a high-quality question bank based on the teacher's requirements.

Internally follow these steps:
1. Generate the requested questions with appropriate types and difficulty, following the teacher's instructions.
2. Generate the correct answer for each question except for long-answer type questions.
3. Assign marks in a balanced way based on question type and difficulty.
4. Assign up to 3 short topic as labels for each question.

Rules:
- Match the requested grade, subject, difficulty, and teacher instructions.
- MCQ: exactly 4 options with exactly 1 correct answer (set is_correct true on that option only).
- Short: no options; put the answer in correct_answer.
- Long: no options; leave correct_answer empty.
- Marks weightage: long >= short >= mcq
- labels: 1–3 short topic tags per question (e.g. "optics", "electricity"); lowercase preferred.

Return ONLY valid JSON. No markdown, explanations, or intermediate reasoning.

Output schema:
{
  "questions": [
    {
      "question_type": "mcq" | "short" | "long",
      "text": "question text",
      "options": [
        {"text": "option text", "is_correct": true}
      ],
      "difficulty": "easy" | "medium" | "hard",
      "labels": ["label1", "label2"],
      "correct_answer": "answer text",
      "marks": 1
    }
  ],
  "total_marks": 20
}
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
