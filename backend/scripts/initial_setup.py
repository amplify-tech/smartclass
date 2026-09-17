#!/usr/bin/env python
"""Bootstrap local data: superuser, grades (classes), and subjects."""

import os
import sys

import django

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from document.models import Grade, Subject
from user.models import User

DEFAULT_SUPERUSER_EMAIL = os.environ.get('SETUP_SUPERUSER_EMAIL', 'admin@smartclass.local')
DEFAULT_SUPERUSER_PASSWORD = os.environ.get('SETUP_SUPERUSER_PASSWORD', 'admin123')

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


def run_setup():
    print('=== Initial setup ===')
    create_superuser()
    create_grades()
    create_subjects()
    print('=== Setup complete ===')


if __name__ == '__main__':
    run_setup()
