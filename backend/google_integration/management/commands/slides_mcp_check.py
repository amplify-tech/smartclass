"""Run the Slides MCP server end to end through the MCP client.

Creates a real presentation in the shared Google account:

    python manage.py slides_mcp_check
    python manage.py slides_mcp_check --title "Demo deck" --url http://127.0.0.1:8001/mcp
"""

import asyncio
import json

from django.core.management.base import BaseCommand, CommandError

from google_integration.mcp_client import MCPClientError, SlidesMCPClient


class Command(BaseCommand):
    help = (
        'Connect to the Slides MCP server and run the presentation path: '
        'create_presentation, add_slide, update_slide, and get_presentation.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--title', default='SmartClass MCP client check')
        parser.add_argument(
            '--slide-title',
            default='Welcome',
        )
        parser.add_argument(
            '--body',
            default='Hello from the SmartClass MCP client.',
        )
        parser.add_argument(
            '--url',
            default=None,
            help='Streamable-http server URL. Defaults to SLIDES_MCP_URL, '
                 'or a stdio subprocess when that is empty.',
        )

    def handle(self, *args, **options):
        try:
            results = asyncio.run(run_check(
                title=options['title'],
                slide_title=options['slide_title'],
                body=options['body'],
                url=options['url'],
            ))
        except MCPClientError as exc:
            raise CommandError(str(exc)) from exc

        for step, result in results.items():
            self.stdout.write(self.style.MIGRATE_HEADING(step))
            self.stdout.write(json.dumps(result, indent=2))
        self.stdout.write(self.style.SUCCESS('Slides MCP check passed.'))


async def run_check(title, slide_title, body, url=None):
    """Return each step's result keyed by step name."""
    async with SlidesMCPClient(url=url) as client:
        tools = await client.list_tools()
        results = {'list_tools': [tool['name'] for tool in tools]}

        presentation = await client.call_tool(
            'create_presentation', {'title': title},
        )
        results['create_presentation'] = presentation
        presentation_id = presentation['presentation_id']

        slide = await client.call_tool('add_slide', {
            'presentation_id': presentation_id,
            'layout': 'TITLE_AND_BODY',
        })
        results['add_slide'] = slide

        results['update_slide'] = await client.call_tool('update_slide', {
            'presentation_id': presentation_id,
            'slide_id': slide['slide_id'],
            'title': slide_title,
            'body': body,
        })

        results['get_presentation'] = await client.call_tool(
            'get_presentation', {'presentation_id': presentation_id},
        )
    return results
