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
        'Connect to the Slides MCP server, list tools, and call ping, '
        'create_presentation, add_slide, and add_text.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--title', default='SmartClass MCP client check')
        parser.add_argument(
            '--text',
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
                text=options['text'],
                url=options['url'],
            ))
        except MCPClientError as exc:
            raise CommandError(str(exc)) from exc

        for step, result in results.items():
            self.stdout.write(self.style.MIGRATE_HEADING(step))
            self.stdout.write(json.dumps(result, indent=2))
        self.stdout.write(self.style.SUCCESS('Slides MCP check passed.'))


async def run_check(title, text, url=None):
    """Return each step's result keyed by step name."""
    async with SlidesMCPClient(url=url) as client:
        tools = await client.list_tools()
        results = {'list_tools': [tool['name'] for tool in tools]}

        results['ping'] = await client.call_tool('ping')

        presentation = await client.call_tool(
            'create_presentation', {'title': title},
        )
        results['create_presentation'] = presentation

        slide = await client.call_tool('add_slide', {
            'presentation_id': presentation['presentation_id'],
        })
        results['add_slide'] = slide

        results['add_text'] = await client.call_tool('add_text', {
            'presentation_id': presentation['presentation_id'],
            'slide_id': slide['slide_id'],
            'text': text,
        })
    return results
