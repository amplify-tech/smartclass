"""Helpers to parse LLM JSON into question dicts."""
import json
import re

from exam.models import Difficulty, QuestionType

VALID_TYPES = {c.value for c in QuestionType}
VALID_DIFFICULTY = {c.value for c in Difficulty}


def parse_questions(raw: str) -> list[dict]:
    data = _extract_json(raw)
    questions = data.get('questions')
    if not isinstance(questions, list) or not questions:
        raise ValueError('llm response missing questions')

    return [_clean_question(q) for q in questions]


def _extract_json(raw: str) -> dict:
    text = (raw or '').strip()
    if not text:
        raise ValueError('empty llm output')

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError('could not parse llm json')
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError('could not parse llm json')
    return data


def _clean_question(item: dict) -> dict:
    q_type = str(item.get('question_type', '')).lower()
    if q_type not in VALID_TYPES:
        raise ValueError(f'bad question_type: {q_type}')

    text = str(item.get('text', '')).strip()
    if not text:
        raise ValueError('question text required')

    try:
        marks = max(1, int(item.get('marks', 1)))
    except (TypeError, ValueError):
        marks = 1

    difficulty = str(item.get('difficulty', Difficulty.MEDIUM)).lower()
    if difficulty not in VALID_DIFFICULTY:
        difficulty = Difficulty.MEDIUM

    correct_answer = str(item.get('correct_answer') or '').strip()
    options = []
    labels = _clean_labels(item.get('labels'))

    if q_type == QuestionType.MCQ:
        options = _clean_options(item.get('options') or [])
        if not correct_answer:
            correct_answer = next(
                (o['text'] for o in options if o['is_correct']),
                '',
            )

    return {
        'question_type': q_type,
        'text': text,
        'marks': marks,
        'difficulty': difficulty,
        'correct_answer': correct_answer,
        'options': options,
        'labels': labels,
    }


def _clean_labels(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []

    cleaned = []
    seen = set()
    for item in raw:
        name = str(item or '').strip()
        if not name:
            continue
        name = name[:64]
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(name)
        if len(cleaned) >= 3:
            break
    return cleaned


def _clean_options(options) -> list[dict]:
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError('mcq needs options')

    cleaned = []
    for i, opt in enumerate(options, start=1):
        text = str(opt.get('text', '')).strip()
        if not text:
            raise ValueError('empty option text')
        cleaned.append({
            'text': text,
            'is_correct': bool(opt.get('is_correct', False)),
            'order': i,
        })

    if not any(o['is_correct'] for o in cleaned):
        cleaned[0]['is_correct'] = True
    return cleaned
