"""Parse and validate the LLM's structured presentation plan.

A plan is one of::

    {'intent': 'create', 'title': str, 'slides': [{'title', 'body', 'image_url'}]}
    {'intent': 'update', 'actions': [{'operation', 'slide_number', 'title',
                                      'body', 'text', 'image_url'}]}

Missing optional fields are ``None``. Slide numbers are 1-based and are
checked against the presentation the LLM was shown.
"""

import json
import re

from presentation.constants import (
    MAX_ACTIONS,
    MAX_CREATE_SLIDES,
    MAX_TEXT_LENGTH,
    MAX_TITLE_LENGTH,
)

CREATE = 'create'
UPDATE = 'update'

ADD_SLIDE = 'add_slide'
UPDATE_SLIDE = 'update_slide'
DELETE_SLIDE = 'delete_slide'
ADD_TEXT = 'add_text'
ADD_IMAGE = 'add_image'
OPERATIONS = (ADD_SLIDE, UPDATE_SLIDE, DELETE_SLIDE, ADD_TEXT, ADD_IMAGE)
_TARGETS_SLIDE = (UPDATE_SLIDE, DELETE_SLIDE, ADD_TEXT, ADD_IMAGE)


class PlanError(ValueError):
    """The LLM plan cannot be carried out; the message is safe to show."""


def parse_plan(raw, instruction, slide_count=None):
    """Return a validated plan.

    ``slide_count`` is the selected presentation's slide count, or ``None``
    when no presentation is selected (only CREATE is allowed then).
    """
    data = _load_json(raw)
    intent = str(data.get('intent') or '').strip().lower()
    if slide_count is None or intent == CREATE:
        return _create_plan(data, instruction)
    if intent != UPDATE:
        raise PlanError('Could not tell whether to create or update a presentation.')
    return _update_plan(data, instruction, slide_count)


def _create_plan(data, instruction):
    title = _text(data.get('title'), MAX_TITLE_LENGTH)
    if not title:
        raise PlanError('The generated presentation has no title.')

    slides = data.get('slides')
    if not isinstance(slides, list) or not slides:
        raise PlanError('The generated presentation has no slides.')
    if len(slides) > MAX_CREATE_SLIDES:
        raise PlanError(f'A presentation can have at most {MAX_CREATE_SLIDES} slides.')

    cleaned = []
    for item in slides:
        item = item if isinstance(item, dict) else {}
        slide = {
            'title': _text(item.get('title'), MAX_TITLE_LENGTH),
            'body': _text(item.get('body'), MAX_TEXT_LENGTH),
            # Generated decks drop unknown URLs rather than fail.
            'image_url': _image_url(item.get('image_url'), instruction, strict=False),
        }
        if not (slide['title'] or slide['body']):
            raise PlanError('A generated slide has no title or text.')
        cleaned.append(slide)
    return {'intent': CREATE, 'title': title, 'slides': cleaned}


def _update_plan(data, instruction, slide_count):
    actions = data.get('actions')
    if not isinstance(actions, list) or not actions:
        raise PlanError('Could not work out what to change in the presentation.')
    if len(actions) > MAX_ACTIONS:
        raise PlanError(f'At most {MAX_ACTIONS} changes can be made at once.')

    cleaned = [_action(item, instruction, slide_count) for item in actions]

    deleted = [a['slide_number'] for a in cleaned if a['operation'] == DELETE_SLIDE]
    if len(deleted) != len(set(deleted)):
        raise PlanError('The same slide is deleted more than once.')
    changed = {
        a['slide_number']
        for a in cleaned
        if a['operation'] in _TARGETS_SLIDE and a['operation'] != DELETE_SLIDE
    }
    deleted = set(deleted)
    if deleted & changed:
        number = min(deleted & changed)
        raise PlanError(f'Slide {number} is deleted and changed in the same request.')
    return {'intent': UPDATE, 'actions': cleaned}


def _action(item, instruction, slide_count):
    item = item if isinstance(item, dict) else {}
    operation = str(item.get('operation') or '').strip().lower()
    if operation not in OPERATIONS:
        raise PlanError(f'Unsupported presentation change {operation or "(none)"!r}.')

    action = {
        'operation': operation,
        'slide_number': None,
        'title': _text(item.get('title'), MAX_TITLE_LENGTH),
        'body': _text(item.get('body'), MAX_TEXT_LENGTH),
        'text': _text(item.get('text'), MAX_TEXT_LENGTH),
        'image_url': None,
    }

    if operation in _TARGETS_SLIDE:
        action['slide_number'] = _slide_number(item.get('slide_number'), slide_count)

    if operation == ADD_SLIDE:
        action['image_url'] = _image_url(item.get('image_url'), instruction, strict=False)
        if not (action['title'] or action['body'] or action['image_url']):
            raise PlanError('A new slide needs a title, text, or image.')
    elif operation == UPDATE_SLIDE:
        if not (action['title'] or action['body']):
            raise PlanError(f'No new title or text for slide {action["slide_number"]}.')
    elif operation == ADD_TEXT:
        action['text'] = action['text'] or action['body']
        if not action['text']:
            raise PlanError(f'No text to add to slide {action["slide_number"]}.')
    elif operation == ADD_IMAGE:
        action['image_url'] = _image_url(item.get('image_url'), instruction, strict=True)
    return action


def _slide_number(value, slide_count):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise PlanError('A slide number is required for this change.') from None
    if not 1 <= number <= slide_count:
        raise PlanError(
            f'Slide {number} does not exist; the presentation has {slide_count} slide(s).'
        )
    return number


def _image_url(value, instruction, strict):
    url = _text(value, 2048)
    if url and url.startswith(('http://', 'https://')) and url in (instruction or ''):
        return url
    if strict:
        raise PlanError('Include the image URL (http or https) in your instruction.')
    return None


def _text(value, limit):
    if isinstance(value, list):
        value = '\n'.join(str(line).strip() for line in value if str(line).strip())
    if value is None:
        return None
    text = str(value).strip()
    return text[:limit] if text else None


def _load_json(raw):
    text = (raw or '').strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        try:
            data = json.loads(match.group(0)) if match else None
        except json.JSONDecodeError:
            data = None
    if not isinstance(data, dict):
        raise PlanError('Could not understand the generated plan. Please try again.')
    return data
