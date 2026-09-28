import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from presentation.chat import ChatService
from presentation.models import Conversation, Message, Presentation
from presentation.plan import PlanError, parse_plan

IMAGE = 'https://example.com/lens.png'


def plan(data, instruction='', slide_count=None):
    return parse_plan(json.dumps(data), instruction, slide_count)


class CreatePlanTests(SimpleTestCase):
    def test_create_without_selected_presentation(self):
        result = plan({
            'intent': 'update',
            'title': 'Optics',
            'slides': [
                {'title': 'Optics', 'body': 'Class 6 Physics'},
                {'title': 'Reflection', 'body': ['Light bounces', 'Angles are equal']},
            ],
        })
        self.assertEqual(result['intent'], 'create')
        self.assertEqual(result['slides'][1]['body'], 'Light bounces\nAngles are equal')

    def test_drops_image_url_not_in_instruction(self):
        result = plan({
            'intent': 'create',
            'title': 'Optics',
            'slides': [{'title': 'Lens', 'image_url': 'https://invented.example/x.png'}],
        })
        self.assertIsNone(result['slides'][0]['image_url'])

    def test_requires_slides(self):
        with self.assertRaises(PlanError):
            plan({'intent': 'create', 'title': 'Optics', 'slides': []})


class UpdatePlanTests(SimpleTestCase):
    def test_update_slide_text(self):
        result = plan(
            {'intent': 'update', 'actions': [
                {'operation': 'update_slide', 'slide_number': '5', 'body': 'Friction'},
            ]},
            slide_count=5,
        )
        self.assertEqual(result['actions'][0]['slide_number'], 5)
        self.assertEqual(result['actions'][0]['body'], 'Friction')

    def test_rejects_missing_slide(self):
        with self.assertRaisesRegex(PlanError, 'Slide 6 does not exist'):
            plan(
                {'intent': 'update', 'actions': [
                    {'operation': 'delete_slide', 'slide_number': 6},
                ]},
                slide_count=5,
            )

    def test_rejects_unknown_operation(self):
        with self.assertRaises(PlanError):
            plan(
                {'intent': 'update', 'actions': [{'operation': 'delete_presentation'}]},
                slide_count=2,
            )

    def test_add_image_needs_url_from_instruction(self):
        action = {'operation': 'add_image', 'slide_number': 1, 'image_url': IMAGE}
        with self.assertRaises(PlanError):
            plan({'intent': 'update', 'actions': [action]}, 'Add a lens', 2)
        result = plan({'intent': 'update', 'actions': [action]}, f'Add {IMAGE}', 2)
        self.assertEqual(result['actions'][0]['image_url'], IMAGE)

    def test_rejects_changing_a_deleted_slide(self):
        with self.assertRaises(PlanError):
            plan(
                {'intent': 'update', 'actions': [
                    {'operation': 'update_slide', 'slide_number': 2, 'title': 'New'},
                    {'operation': 'delete_slide', 'slide_number': 2},
                ]},
                slide_count=3,
            )

    def test_create_intent_with_selected_presentation(self):
        result = plan(
            {'intent': 'create', 'title': 'Lenses', 'slides': [{'title': 'Lenses'}]},
            slide_count=3,
        )
        self.assertEqual(result['intent'], 'create')

    def test_parses_json_wrapped_in_text(self):
        raw = 'Sure: {"intent": "update", "actions": [{"operation": "delete_slide", "slide_number": 1}]}'
        self.assertEqual(parse_plan(raw, '', 2)['actions'][0]['operation'], 'delete_slide')


class ChatServiceTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(email='t@example.com', password='x')
        self.conversation = Conversation.objects.create(created_by=user)
        for index, title in enumerate(('Optics', 'Photosynthesis')):
            Presentation.objects.create(
                created_by=user,
                conversation=self.conversation,
                google_presentation_id=f'g{index}',
                title=title,
                url=f'https://docs.google.com/presentation/d/g{index}/edit',
            )

    def send(self, llm_output, content='Add a slide about reflection'):
        with patch('presentation.chat.get_llm_provider') as provider:
            provider.return_value.generate.return_value = json.dumps(llm_output)
            return ChatService().send(self.conversation, content)

    def test_reply_is_saved_with_user_message(self):
        reply = self.send({'action': 'reply', 'reply': 'Hello!'}, 'Hi')
        self.assertEqual(reply.content, 'Hello!')
        self.assertEqual(
            list(self.conversation.messages.values_list('role', flat=True)),
            [Message.USER, Message.ASSISTANT],
        )
        self.assertEqual(Conversation.objects.get().title, 'Hi')

    def test_asks_which_presentation_when_target_unknown(self):
        with patch('presentation.chat.PresentationService') as service:
            reply = self.send({'action': 'update', 'presentation_id': None})
        service.return_value.run_prompt.assert_not_called()
        self.assertIn('Which presentation', reply.content)
        self.assertIn('Photosynthesis', reply.content)
