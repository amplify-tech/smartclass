"""Presentation chat: teacher message -> LLM picks an action -> PresentationService.

The LLM sees recent history and the chat's presentations, so follow-ups like
"add a slide about reflection" reach the right deck. All Slides work still
goes through ``PresentationService`` and the Slides MCP server.
"""

import logging

from rest_framework.exceptions import APIException, ValidationError

from common.constants import JSON
from common.llm.factory import get_llm_provider
from presentation.constants import CHAT_HISTORY_MESSAGES
from presentation.exceptions import PresentationCommandFailed
from presentation.models import Message
from presentation.plan import PlanError, load_json
from presentation.prompts import CHAT_SYSTEM_PROMPT, build_chat_prompt
from presentation.services import PresentationService

logger = logging.getLogger(__name__)

CREATE = 'create'
UPDATE = 'update'
INFO = 'info'
DELETE = 'delete'
REPLY = 'reply'
_NEEDS_PRESENTATION = (UPDATE, INFO, DELETE)

_FALLBACK_REPLY = 'Sorry, I could not understand that. Could you rephrase it?'


class ChatService:
    def send(self, conversation, content):
        """Save the teacher message, act on it, and save the assistant reply."""
        history = [
            (m.role, m.content)
            for m in conversation.messages.order_by('-created_at', '-id')[:CHAT_HISTORY_MESSAGES]
        ][::-1]
        Message.objects.create(conversation=conversation, role=Message.USER, content=content)

        presentation, is_error = None, False
        try:
            reply, presentation = self._respond(conversation, content, history)
        except PresentationCommandFailed as exc:
            presentation = self._attach(conversation, exc.presentation)
            reply, is_error = str(exc.detail), True
        except APIException as exc:
            reply, is_error = _error_text(exc), True

        if not conversation.title:
            conversation.title = content[:80]
        conversation.save(update_fields=['title', 'updated_at'])
        return Message.objects.create(
            conversation=conversation,
            role=Message.ASSISTANT,
            content=reply,
            presentation=presentation,
            is_error=is_error,
        )

    def _respond(self, conversation, content, history):
        presentations = list(conversation.presentations.all())
        decision = self._decide(conversation, content, history, presentations)
        action = decision['action']

        if action == REPLY:
            return decision['reply'] or _FALLBACK_REPLY, None

        instruction = decision['instruction'] or content
        service = PresentationService()
        if action == CREATE:
            record, result = service.run_prompt(conversation.created_by, instruction)
            record = self._attach(conversation, record)
            return f'Created "{record.title}" with {_slides(result["slides"])}.', record

        target = next((p for p in presentations if p.id == decision['presentation_id']), None)
        if target is None:
            return _which_presentation(presentations), None

        if action == UPDATE:
            record, result = service.run_prompt(conversation.created_by, instruction, target)
            record = self._attach(conversation, record)
            if record.id != target.id:
                return f'Created a new presentation "{record.title}" with {_slides(result["slides"])}.', record
            return f'Updated "{record.title}". It now has {_slides(result["slides"])}.', record

        if action == INFO:
            slides = service.get_slides(target)
            lines = [f'"{target.title}" has {_slides(slides)}:']
            for number, slide in enumerate(slides, start=1):
                first = next((l.strip() for l in slide['text'].splitlines() if l.strip()), '(empty)')
                lines.append(f'{number}. {first[:80]}')
            return '\n'.join(lines), target

        title = target.title
        service.delete(target)
        return f'Deleted the presentation "{title}".', None

    def _decide(self, conversation, content, history, presentations):
        last_used = (
            conversation.messages
            .filter(role=Message.ASSISTANT, presentation__isnull=False)
            .order_by('-created_at', '-id')
            .values_list('presentation_id', flat=True)
            .first()
        )
        try:
            raw = get_llm_provider().generate(
                system_prompt=CHAT_SYSTEM_PROMPT,
                user_prompt=build_chat_prompt(content, history, presentations, last_used),
                response_format=JSON,
            )
            data = load_json(raw)
        except PlanError:
            data = {}
        except Exception:
            logger.exception('presentation chat LLM call failed')
            raise ValidationError('Could not process your message. Please try again.')

        action = str(data.get('action') or '').strip().lower()
        if action not in (CREATE, UPDATE, INFO, DELETE, REPLY):
            action = REPLY
        presentation_id = None
        if action in _NEEDS_PRESENTATION:
            presentation_id = _pick_presentation(data.get('presentation_id'), content, presentations)

        logger.info('presentation chat action=%s presentation=%s', action, presentation_id)
        return {
            'action': action,
            'presentation_id': presentation_id,
            'instruction': str(data.get('instruction') or '').strip(),
            'reply': str(data.get('reply') or '').strip(),
        }

    @staticmethod
    def _attach(conversation, record):
        if record is not None and record.conversation_id != conversation.id:
            record.conversation = conversation
            record.save(update_fields=['conversation', 'updated_at'])
        return record


def _pick_presentation(value, content, presentations):
    """The LLM's choice if it is a real ID, else a title named in the message, else the only one."""
    ids = {p.id for p in presentations}
    try:
        if int(value) in ids:
            return int(value)
    except (TypeError, ValueError):
        pass
    text = content.lower()
    named = [p.id for p in presentations if p.title.lower() in text]
    if len(named) == 1:
        return named[0]
    if len(presentations) == 1:
        return presentations[0].id
    return None


def _which_presentation(presentations):
    if not presentations:
        return 'There is no presentation in this chat yet. Ask me to create one first.'
    titles = '\n'.join(f'- {p.title}' for p in presentations)
    return f'Which presentation do you mean?\n{titles}'


def _slides(slides):
    return f'{len(slides)} slide{"" if len(slides) == 1 else "s"}'


def _error_text(exc):
    detail = exc.detail
    while isinstance(detail, (list, dict)) and detail:
        detail = next(iter(detail.values())) if isinstance(detail, dict) else detail[0]
    return str(detail) or 'Something went wrong. Please try again.'
