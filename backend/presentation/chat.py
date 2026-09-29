"""Presentation chat handler: teacher message -> LLM picks an action -> PresentationService.

The LLM sees recent history and the chat's presentations, so follow-ups like
"add a slide about reflection" reach the right deck. All Slides work still
goes through ``PresentationService`` and the Slides MCP server. Storing the
messages and context is ``chat.services.ChatService``'s job.

Conversation context::

    {'presentations': [{'id', 'title', 'url'}], 'active_presentation_id': id}
"""

import logging

from rest_framework.exceptions import APIException, ValidationError

from chat.handlers import ChatHandler, ChatReply
from common.constants import JSON
from common.llm.factory import get_llm_provider
from presentation.constants import CHAT_HISTORY_MESSAGES
from presentation.exceptions import PresentationCommandFailed
from presentation.models import Presentation
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


class PresentationChatHandler(ChatHandler):
    def respond(self, conversation, content, history):
        user = conversation.created_by
        active_id = conversation.context.get('active_presentation_id')
        presentations = _load(user, [p['id'] for p in conversation.context.get('presentations', [])])

        is_error = False
        try:
            reply, touched = self._respond(user, content, history, presentations, active_id)
        except PresentationCommandFailed as exc:
            reply, touched, is_error = str(exc.detail), exc.presentation, True
        except APIException as exc:
            reply, touched, is_error = _error_text(exc), None, True

        ids = [p.id for p in presentations]
        if touched is not None:
            active_id = touched.id
            if touched.id not in ids:
                ids.append(touched.id)
        return ChatReply(reply, is_error=is_error, context=_context(_load(user, ids), active_id))

    def _respond(self, user, content, history, presentations, active_id):
        """Return ``(reply, presentation the reply is about or None)``."""
        decision = self._decide(content, history, presentations, active_id)
        action = decision['action']

        if action == REPLY:
            return decision['reply'] or _FALLBACK_REPLY, None

        instruction = decision['instruction'] or content
        service = PresentationService()
        if action == CREATE:
            record, result = service.run_prompt(user, instruction)
            return f'Created "{record.title}" with {_slides(result["slides"])}.\n{record.url}', record

        target = next((p for p in presentations if p.id == decision['presentation_id']), None)
        if target is None:
            return _which_presentation(presentations), None

        if action == UPDATE:
            record, result = service.run_prompt(user, instruction, target)
            if record.id != target.id:
                return (
                    f'Created a new presentation "{record.title}" with {_slides(result["slides"])}.\n{record.url}',
                    record,
                )
            return f'Updated "{record.title}". It now has {_slides(result["slides"])}.\n{record.url}', record

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

    def _decide(self, content, history, presentations, active_id):
        try:
            raw = get_llm_provider().generate(
                system_prompt=CHAT_SYSTEM_PROMPT,
                user_prompt=build_chat_prompt(
                    content, history[-CHAT_HISTORY_MESSAGES:], presentations, active_id,
                ),
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


def _load(user, ids):
    """The user's presentations with these IDs, in order; deleted ones are dropped."""
    by_id = Presentation.objects.filter(created_by=user).in_bulk(ids)
    return [by_id[i] for i in ids if i in by_id]


def _context(presentations, active_id):
    ids = {p.id for p in presentations}
    return {
        'presentations': [{'id': p.id, 'title': p.title, 'url': p.url} for p in presentations],
        'active_presentation_id': active_id if active_id in ids else None,
    }


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
