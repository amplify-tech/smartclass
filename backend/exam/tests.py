from django.contrib.auth import get_user_model
from django.test import TestCase

from document.models import Grade, Subject
from exam.models import Option, Question, QuestionType
from exam.serializers import QuestionSerializer

User = get_user_model()


class QuestionSerializerOptionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='teacher@example.com',
            password='test-pass-123',
        )
        self.grade = Grade.objects.create(name='10th', order=10)
        self.subject = Subject.objects.create(name='Physics')

    def _base_payload(self, **overrides):
        data = {
            'text': 'What is reflection of light?',
            'question_type': QuestionType.MCQ,
            'difficulty': 'easy',
            'marks': 1,
            'grade': self.grade.id,
            'subject': self.subject.id,
            'correct_answer': 'A',
            'options': [
                {'text': 'Bouncing of light', 'is_correct': True, 'order': 1},
                {'text': 'Bending of light', 'is_correct': False, 'order': 2},
                {'text': 'Absorption of light', 'is_correct': False, 'order': 3},
                {'text': 'Emission of light', 'is_correct': False, 'order': 4},
            ],
        }
        data.update(overrides)
        return data

    def test_create_mcq_persists_options(self):
        serializer = QuestionSerializer(data=self._base_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)
        question = serializer.save(created_by=self.user)

        options = list(question.options.order_by('order'))
        self.assertEqual(len(options), 4)
        self.assertEqual(options[0].text, 'Bouncing of light')
        self.assertTrue(options[0].is_correct)
        self.assertEqual(sum(1 for o in options if o.is_correct), 1)

    def test_create_mcq_requires_options(self):
        payload = self._base_payload()
        del payload['options']
        serializer = QuestionSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn('options', serializer.errors)

    def test_create_short_rejects_options(self):
        serializer = QuestionSerializer(
            data=self._base_payload(
                question_type=QuestionType.SHORT,
                correct_answer='Light bouncing from a surface.',
            ),
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('options', serializer.errors)

    def test_update_replaces_options(self):
        serializer = QuestionSerializer(data=self._base_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)
        question = serializer.save(created_by=self.user)

        update = QuestionSerializer(
            question,
            data={
                'options': [
                    {'text': 'New A', 'is_correct': False, 'order': 1},
                    {'text': 'New B', 'is_correct': True, 'order': 2},
                ],
            },
            partial=True,
        )
        self.assertTrue(update.is_valid(), update.errors)
        update.save()

        options = list(question.options.order_by('order'))
        self.assertEqual(len(options), 2)
        self.assertEqual(options[1].text, 'New B')
        self.assertTrue(options[1].is_correct)
        self.assertEqual(Option.objects.filter(question=question).count(), 2)

    def test_update_to_short_clears_options(self):
        serializer = QuestionSerializer(data=self._base_payload())
        self.assertTrue(serializer.is_valid(), serializer.errors)
        question = serializer.save(created_by=self.user)

        update = QuestionSerializer(
            question,
            data={
                'question_type': QuestionType.SHORT,
                'correct_answer': 'Bouncing of light from a surface.',
            },
            partial=True,
        )
        self.assertTrue(update.is_valid(), update.errors)
        update.save()

        question.refresh_from_db()
        self.assertEqual(question.question_type, QuestionType.SHORT)
        self.assertEqual(question.options.count(), 0)

    def test_create_short_without_options(self):
        serializer = QuestionSerializer(
            data={
                'text': 'State Ohm\'s law.',
                'question_type': QuestionType.SHORT,
                'difficulty': 'medium',
                'marks': 2,
                'grade': self.grade.id,
                'subject': self.subject.id,
                'correct_answer': 'V = IR',
            },
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        question = serializer.save(created_by=self.user)
        self.assertEqual(question.question_type, QuestionType.SHORT)
        self.assertEqual(question.options.count(), 0)
        self.assertEqual(Question.objects.count(), 1)
