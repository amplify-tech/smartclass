#!/usr/bin/env python
"""Bootstrap local data: superuser, grades (classes), subjects, and sample questions."""

import os
import sys

import django

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from document.models import Grade, Subject
from exam.models import Difficulty, Label, Question, QuestionType
from user.models import User

DEFAULT_SUPERUSER_EMAIL = os.environ.get('SETUP_SUPERUSER_EMAIL', 'admin@smartclass.local')
DEFAULT_SUPERUSER_PASSWORD = os.environ.get('SETUP_SUPERUSER_PASSWORD', 'admin123')

DEFAULT_DUMMY_USER_EMAIL = os.environ.get('SETUP_DUMMY_USER_EMAIL', 'teacher@smartclass.local')
DEFAULT_DUMMY_USER_PASSWORD = os.environ.get('SETUP_DUMMY_USER_PASSWORD', 'teacher123')

GRADES = [
    ('6th', 6),
    ('7th', 7),
    ('8th', 8),
    ('9th', 9),
    ('10th', 10),
    ('11th', 11),
    ('12th', 12),
]

SUBJECTS = [
    'Mathematics',
    'Science',
    'English',
    'Physics',
    'Chemistry',
    'Biology',
    'History',
    'Geography',
    'Computer Science',
]

DUMMY_QUESTION_LABELS = ['number system', 'add']

DUMMY_QUESTIONS = [
    {
        'text': 'what is 6+8=?',
        'correct_answer': '14',
    },
    {
        'text': 'what is 7+2=?',
        'correct_answer': '9',
    },
]


def create_superuser(email=None, password=None):
    """Create a superuser if one with this email does not already exist."""
    email = email or DEFAULT_SUPERUSER_EMAIL
    password = password or DEFAULT_SUPERUSER_PASSWORD

    existing = User.objects.filter(email=email).first()
    if existing:
        if not existing.is_superuser:
            existing.is_staff = True
            existing.is_superuser = True
            existing.save(update_fields=['is_staff', 'is_superuser'])
            print(f'Promoted existing user to superuser: {email}')
        else:
            print(f'Superuser already exists: {email}')
        return existing

    user = User.objects.create_superuser(email=email, password=password)
    print(f'Created superuser: {email}')
    return user


def create_dummy_user(email=None, password=None):
    """Create a regular teacher user for local testing."""
    email = email or DEFAULT_DUMMY_USER_EMAIL
    password = password or DEFAULT_DUMMY_USER_PASSWORD

    existing = User.objects.filter(email=email).first()
    if existing:
        print(f'Dummy user already exists: {email}')
        return existing

    user = User.objects.create_user(email=email, password=password)
    print(f'Created dummy user: {email}')
    return user


def create_grades():
    """Seed school grades / class levels."""
    created_count = 0
    for name, order in GRADES:
        _, created = Grade.objects.get_or_create(
            name=name,
            defaults={'order': order},
        )
        if created:
            created_count += 1
            print(f'Created grade: {name}')
        else:
            print(f'Grade already exists: {name}')
    print(f'Grades done ({created_count} new, {len(GRADES)} total listed)')


def create_subjects():
    """Seed academic subjects."""
    created_count = 0
    for name in SUBJECTS:
        _, created = Subject.objects.get_or_create(name=name)
        if created:
            created_count += 1
            print(f'Created subject: {name}')
        else:
            print(f'Subject already exists: {name}')
    print(f'Subjects done ({created_count} new, {len(SUBJECTS)} total listed)')


def create_dummy_questions(created_by):
    """Seed two 6th-grade Mathematics short-answer questions with topic labels."""
    grade = Grade.objects.get(name='6th')
    subject = Subject.objects.get(name='Mathematics')

    labels = []
    for name in DUMMY_QUESTION_LABELS:
        label, created = Label.objects.get_or_create(name=name)
        labels.append(label)
        if created:
            print(f'Created label: {name}')
        else:
            print(f'Label already exists: {name}')

    created_count = 0
    for item in DUMMY_QUESTIONS:
        question, created = Question.objects.get_or_create(
            text=item['text'],
            grade=grade,
            subject=subject,
            defaults={
                'question_type': QuestionType.SHORT,
                'difficulty': Difficulty.EASY,
                'marks': 1,
                'correct_answer': item['correct_answer'],
                'created_by': created_by,
            },
        )
        if created:
            created_count += 1
            print(f'Created question: {item["text"]}')
        else:
            print(f'Question already exists: {item["text"]}')
        question.labels.set(labels)

    print(f'Dummy questions done ({created_count} new, {len(DUMMY_QUESTIONS)} total listed)')


def run_setup():
    print('=== Initial setup ===')
    create_superuser()
    dummy_user = create_dummy_user()
    create_grades()
    create_subjects()
    create_dummy_questions(created_by=dummy_user)
    print('=== Setup complete ===')


if __name__ == '__main__':
    run_setup()
