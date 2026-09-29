import json

from django.test import SimpleTestCase

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

    def test_rejects_add_text(self):
        with self.assertRaises(PlanError):
            plan(
                {'intent': 'update', 'actions': [
                    {'operation': 'add_text', 'slide_number': 1, 'text': 'Extra'},
                ]},
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

    def test_missing_intent_with_actions_is_an_update(self):
        result = plan(
            {'actions': [{'operation': 'add_slide', 'title': 'DSA', 'body': 'Arrays and trees'}]},
            slide_count=4,
        )
        self.assertEqual(result['intent'], 'update')
        self.assertEqual(result['actions'][0]['operation'], 'add_slide')
        self.assertEqual(result['actions'][0]['title'], 'DSA')

    def test_bare_add_slide_is_an_update(self):
        result = plan(
            {'operation': 'add_slide', 'title': 'DSA', 'body': 'Stacks and queues'},
            slide_count=4,
        )
        self.assertEqual(result['actions'][0]['title'], 'DSA')
        self.assertIsNone(result['actions'][0]['slide_number'])

    def test_operation_used_as_intent(self):
        result = plan(
            {'intent': 'add_slide', 'title': 'DSA', 'body': 'Graphs'},
            slide_count=2,
        )
        self.assertEqual(result['actions'][0]['operation'], 'add_slide')
        self.assertEqual(result['actions'][0]['body'], 'Graphs')

    def test_slides_while_editing_are_appended(self):
        result = plan(
            {'slides': [{'title': 'DSA', 'body': 'Big-O notation'}]},
            slide_count=3,
        )
        self.assertEqual(result['intent'], 'update')
        self.assertEqual(result['actions'][0]['operation'], 'add_slide')

    def test_update_intent_with_slides_appends(self):
        result = plan(
            {'intent': 'update', 'slides': [{'title': 'DSA', 'body': 'Linked lists'}]},
            slide_count=3,
        )
        self.assertEqual(result['actions'][0]['body'], 'Linked lists')

    def test_single_action_object(self):
        result = plan(
            {'intent': 'update', 'actions': {'operation': 'add_slide', 'title': 'DSA', 'body': 'Heaps'}},
            slide_count=1,
        )
        self.assertEqual(result['actions'][0]['title'], 'DSA')

    def test_still_rejects_unrecognized_update(self):
        with self.assertRaisesRegex(PlanError, 'create or update'):
            plan({'note': 'hello'}, slide_count=2)

    def test_parses_json_wrapped_in_text(self):
        raw = 'Sure: {"intent": "update", "actions": [{"operation": "delete_slide", "slide_number": 1}]}'
        self.assertEqual(parse_plan(raw, '', 2)['actions'][0]['operation'], 'delete_slide')
