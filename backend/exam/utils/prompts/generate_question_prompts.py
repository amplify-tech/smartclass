import json

# Shared output schema for both non-RAG and RAG generation (contract unchanged).
_OUTPUT_SCHEMA = """
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
""".strip()

_SHARED_RULES = """
Rules:
- Match the requested grade, subject, difficulty, and teacher instructions.
- MCQ: exactly 4 options with exactly 1 correct answer (set is_correct true on that option only).
- Short: no options; put the answer in correct_answer.
- Long: no options; leave correct_answer empty.
- Marks weightage: long >= short >= mcq
- labels: 1–3 short topic tags per question (e.g. "optics", "electricity"); lowercase preferred.

Return ONLY valid JSON. No markdown, explanations, or intermediate reasoning.
""".strip()


SYSTEM_PROMPT = f"""You are an expert school exam question generator.

Generate a high-quality question bank based on the teacher's requirements.

Internally follow these steps:
1. Generate the requested questions with appropriate types and difficulty, following the teacher's instructions.
2. Generate the correct answer for each question except for long-answer type questions.
3. Assign marks in a balanced way based on question type and difficulty.
4. Assign up to 3 short topic as labels for each question.

{_SHARED_RULES}

{_OUTPUT_SCHEMA}
"""


RAG_SYSTEM_PROMPT = f"""You are an expert school exam question generator.

Generate a high-quality question bank grounded in the provided source excerpts from the teacher's selected documents.

Internally follow these steps:
1. Use only the provided source excerpts as factual grounding for question content.
2. Generate the requested questions with appropriate types and difficulty, following the teacher's instructions.
3. Generate the correct answer for each question except for long-answer type questions; answers must be supportable from the sources when possible.
4. Assign marks in a balanced way based on question type and difficulty.
5. Assign up to 3 short topic as labels for each question.

{_SHARED_RULES}
- Prefer questions that can be answered from the provided sources; do not invent facts not present in the sources.
- Source/page markers are for your grounding only; do not mention them in question text.

{_OUTPUT_SCHEMA}
"""


def build_user_prompt(
    *,
    grade_name,
    subject_name,
    difficulty,
    total_marks,
    question_types,
    description,
    context=None,
):
    type_counts = question_types if isinstance(question_types, dict) else {}
    total = sum(type_counts.values()) if type_counts else 0
    prompt = (
        f'Grade: {grade_name}\n'
        f'Subject: {subject_name}\n'
        f'Difficulty: {difficulty}\n'
        f'Total marks: {total_marks}\n'
        f'Question types: {json.dumps(type_counts)}\n'
        f'Teacher instruction: {description or "(none)"}\n'
        f'Generate exactly {total} questions.'
    )
    if context is None:
        return prompt
    context_block = context.strip() or '(no relevant excerpts retrieved)'
    return (
        f'{prompt}\n\n'
        f'Source excerpts (use these as grounding):\n'
        f'{context_block}'
    )
