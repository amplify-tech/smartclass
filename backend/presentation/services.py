"""Teacher prompt -> LLM plan -> MCP tool calls -> Google Slides.

The LLM only produces a structured plan (see ``presentation.plan``). Every
Google Slides change goes through the Slides MCP server via
``SlidesMCPClient``; nothing here talks to Google directly.
"""

import asyncio
import logging

from asgiref.sync import async_to_sync
from rest_framework.exceptions import ValidationError

from common.constants import JSON
from common.llm.factory import get_llm_provider
from google_integration.mcp_client import (
    MCPClientError,
    MCPToolError,
    SlidesMCPClient,
)
from presentation.constants import CONTENT_SLIDE_LAYOUT
from presentation.exceptions import (
    PlanGenerationFailed,
    PresentationCommandFailed,
    SlidesUnavailable,
)
from presentation.models import Presentation
from presentation.plan import (
    ADD_IMAGE,
    ADD_SLIDE,
    ADD_TEXT,
    CREATE,
    DELETE_SLIDE,
    UPDATE_SLIDE,
    PlanError,
    parse_plan,
)
from presentation.prompts import (
    CREATE_SYSTEM_PROMPT,
    UPDATE_SYSTEM_PROMPT,
    build_create_prompt,
    build_update_prompt,
)

logger = logging.getLogger(__name__)

# These operations are the MCP tool name plus the extra arguments they need.
_TOOL_ARGUMENTS = {
    DELETE_SLIDE: lambda action: {},
    ADD_TEXT: lambda action: {'text': action['text']},
    ADD_IMAGE: lambda action: {'image_url': action['image_url']},
}


class PresentationService:
    def run_prompt(self, user, instruction, presentation=None):
        """Create or update a presentation from a natural-language instruction.

        Returns ``(record, result)`` where ``result`` holds the intent, the
        live slides, and every MCP tool call that was made.
        """
        google_id = presentation.google_presentation_id if presentation else None
        outcome = {
            'plan': None,
            'created': None,
            'steps': [],
            'title': None,
            'slides': None,
        }
        try:
            _connect(lambda client: _run_prompt(client, instruction, google_id, outcome))
        except PlanError as exc:
            raise ValidationError({'prompt': [str(exc)]}) from exc
        except MCPClientError as exc:
            _raise_slides_error(exc, user, presentation, outcome)

        record = self._save(user, presentation, outcome)
        logger.info(
            'presentation %s %s with %s MCP call(s)',
            record.id, outcome['plan']['intent'], len(outcome['steps']),
        )
        return record, {
            'intent': outcome['plan']['intent'],
            'slides': outcome['slides'],
            'steps': outcome['steps'],
        }

    def get_slides(self, presentation):
        """Live slide list for a stored presentation."""
        try:
            info = _connect(lambda client: client.call_tool('get_presentation', {
                'presentation_id': presentation.google_presentation_id,
            }))
        except MCPClientError as exc:
            _raise_slides_error(exc)
        if info['title'] and info['title'] != presentation.title:
            presentation.title = info['title']
            presentation.save(update_fields=['title', 'updated_at'])
        return info['slides']

    def delete(self, presentation):
        """Delete the Google file, then the record."""
        try:
            _connect(lambda client: client.call_tool('delete_presentation', {
                'presentation_id': presentation.google_presentation_id,
            }))
        except MCPClientError as exc:
            _raise_slides_error(exc)
        presentation.delete()

    @staticmethod
    def _save(user, presentation, outcome):
        created = outcome['created']
        if created:
            return Presentation.objects.create(
                created_by=user,
                google_presentation_id=created['presentation_id'],
                title=created['title'],
                url=created['url'],
            )
        if outcome['title']:
            presentation.title = outcome['title']
        presentation.save(update_fields=['title', 'updated_at'])
        return presentation


def _connect(work):
    """Run ``work(client)`` inside one Slides MCP session."""
    async def run():
        async with SlidesMCPClient() as client:
            return await work(client)

    return async_to_sync(run)()


def _raise_slides_error(exc, user=None, presentation=None, outcome=None):
    """Turn an MCP failure into the error chat already shows.

    A tool error keeps a deck that was created or was already selected.
    A dropped connection does that only after a new deck exists. Before
    that, Slides is reported as unavailable.
    """
    created = outcome.get('created') if outcome else None
    if isinstance(exc, MCPToolError) or created:
        record = None
        steps = []
        if outcome is not None and (created or presentation is not None):
            record = PresentationService._save(user, presentation, outcome)
            steps = outcome['steps']
        logger.warning(
            'presentation MCP call failed after %s step(s): %s',
            len(steps), exc,
        )
        raise PresentationCommandFailed(str(exc), record, steps) from exc
    raise SlidesUnavailable() from exc


async def _run_prompt(client, instruction, google_id, outcome):
    """Fill ``outcome`` as work completes so a failure keeps partial results."""
    context = None
    if google_id:
        context = await client.call_tool(
            'get_presentation', {'presentation_id': google_id},
        )

    plan = await asyncio.to_thread(_plan, instruction, context)
    outcome['plan'] = plan

    if plan['intent'] == CREATE:
        google_id = await _create(client, plan, outcome)
    else:
        await _update(client, plan, context, outcome)

    info = await client.call_tool(
        'get_presentation', {'presentation_id': google_id},
    )
    outcome['slides'] = info['slides']
    outcome['title'] = info['title']


def _plan(instruction, context):
    if context is None:
        system_prompt = CREATE_SYSTEM_PROMPT
        user_prompt = build_create_prompt(instruction)
        slide_count = None
    else:
        system_prompt = UPDATE_SYSTEM_PROMPT
        user_prompt = build_update_prompt(instruction, context)
        slide_count = len(context['slides'])

    try:
        raw = get_llm_provider().generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=JSON,
        )
    except Exception as exc:
        logger.exception('presentation plan LLM call failed')
        raise PlanGenerationFailed() from exc

    try:
        plan = parse_plan(raw, instruction, slide_count)
    except PlanError:
        logger.warning('unusable presentation plan: %s', (raw or '')[:1500])
        raise
    logger.info(
        'presentation plan intent=%s items=%s',
        plan['intent'], len(plan.get('slides') or plan.get('actions') or []),
    )
    return plan


async def _create(client, plan, outcome):
    created = await _step(client, outcome, 'create_presentation', {
        'title': plan['title'],
    })
    presentation_id = created['presentation_id']
    outcome['created'] = {**created, 'title': plan['title']}

    info = await client.call_tool(
        'get_presentation', {'presentation_id': presentation_id},
    )
    # A new deck starts with one title slide; it holds the first planned slide.
    title_slide_id = info['slides'][0]['slide_id'] if info['slides'] else None

    for index, slide in enumerate(plan['slides']):
        if index == 0 and title_slide_id:
            slide_id = title_slide_id
        else:
            slide_id = await _add_slide(client, outcome, presentation_id)
        await _fill_slide(client, outcome, presentation_id, slide_id, slide)
    return presentation_id


async def _update(client, plan, context, outcome):
    presentation_id = context['presentation_id']
    # Resolve numbers before any change so deletes don't shift later actions.
    slide_ids = [slide['slide_id'] for slide in context['slides']]

    for action in plan['actions']:
        operation = action['operation']
        if operation == ADD_SLIDE:
            slide_id = await _add_slide(client, outcome, presentation_id)
            await _fill_slide(client, outcome, presentation_id, slide_id, action)
            continue

        slide_id = slide_ids[action['slide_number'] - 1]
        arguments = {'presentation_id': presentation_id, 'slide_id': slide_id}
        if operation == UPDATE_SLIDE:
            arguments.update(_title_body(action))
        else:
            arguments.update(_TOOL_ARGUMENTS[operation](action))
        await _step(client, outcome, operation, arguments)


async def _add_slide(client, outcome, presentation_id):
    result = await _step(client, outcome, 'add_slide', {
        'presentation_id': presentation_id,
        'layout': CONTENT_SLIDE_LAYOUT,
    })
    return result['slide_id']


async def _fill_slide(client, outcome, presentation_id, slide_id, slide):
    target = {'presentation_id': presentation_id, 'slide_id': slide_id}
    content = _title_body(slide)
    if content:
        await _step(client, outcome, 'update_slide', {**target, **content})
    if slide.get('image_url'):
        await _step(client, outcome, 'add_image', {
            **target, 'image_url': slide['image_url'],
        })


def _title_body(item):
    return {
        key: item[key]
        for key in ('title', 'body')
        if item.get(key)
    }


async def _step(client, outcome, tool, arguments):
    result = await client.call_tool(tool, arguments)
    outcome['steps'].append({'tool': tool, 'arguments': arguments, 'result': result})
    return result
