"""MCP client for the SmartClass Google Slides MCP server (``slides_mcp``).

Everything goes through the MCP protocol; this module never touches the
Google Slides service or Google APIs. By default the server is launched as
a stdio subprocess. Set ``SLIDES_MCP_URL`` to connect to an already running
streamable-http server instead.

Usage::

    async with SlidesMCPClient() as client:
        tools = await client.list_tools()
        result = await client.call_tool('create_presentation', {'title': 'Demo'})

Sync code can wrap a coroutine with ``asyncio.run`` or
``asgiref.sync.async_to_sync``.
"""

import logging
import sys

from django.conf import settings
from mcp import Client, MCPError, StdioServerParameters

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """The MCP server could not be reached or a request failed."""


class MCPToolError(MCPClientError):
    """The MCP server ran the tool and reported an error."""

    def __init__(self, tool_name, message):
        super().__init__(message)
        self.tool_name = tool_name


class SlidesMCPClient:
    """One MCP session with the Slides server for the ``async with`` block."""

    def __init__(self, url=None, timeout_seconds=None):
        self._url = settings.SLIDES_MCP_URL if url is None else url
        self._timeout_seconds = (
            timeout_seconds or settings.SLIDES_MCP_TIMEOUT_SECONDS
        )
        self._client = None

    async def __aenter__(self):
        client = Client(
            self._server(),
            read_timeout_seconds=self._timeout_seconds,
        )
        try:
            await client.__aenter__()
        except Exception as exc:
            logger.warning('Slides MCP connection failed: %r', exc)
            raise MCPClientError(
                f'Could not connect to the Slides MCP server: {_describe(exc)}'
            ) from exc
        self._client = client
        return self

    async def __aexit__(self, exc_type, exc, tb):
        client, self._client = self._client, None
        if client is None:
            return
        try:
            await client.__aexit__(exc_type, exc, tb)
        except Exception as close_exc:
            logger.warning('Slides MCP session did not close cleanly: %r', close_exc)

    async def list_tools(self):
        """Return the server's tools as plain dicts with their JSON schemas."""
        tools = []
        cursor = None
        while True:
            result = await self._request(
                'list tools',
                lambda: self._session().list_tools(cursor=cursor),
            )
            tools.extend(
                {
                    'name': tool.name,
                    'description': tool.description or '',
                    'input_schema': tool.input_schema,
                    'output_schema': tool.output_schema,
                }
                for tool in result.tools
            )
            cursor = result.next_cursor
            if not cursor:
                return tools

    async def call_tool(self, name, arguments=None):
        """Call a tool and return its structured result, or its text if none.

        Raises ``MCPToolError`` when the tool reports an error.
        """
        result = await self._request(
            f'call tool {name!r}',
            lambda: self._session().call_tool(name, arguments or {}),
        )
        text = '\n'.join(
            block.text for block in result.content if block.type == 'text'
        )
        if result.is_error:
            raise MCPToolError(name, text or f'Tool {name!r} failed.')
        if result.structured_content is not None:
            return result.structured_content
        return text

    def _server(self):
        if self._url:
            return self._url
        return StdioServerParameters(
            command=sys.executable,
            args=['-m', 'slides_mcp.server'],
            cwd=str(settings.BASE_DIR),
        )

    def _session(self):
        if self._client is None:
            raise MCPClientError(
                'The Slides MCP client is not connected; use "async with".'
            )
        return self._client

    async def _request(self, action, send):
        try:
            return await send()
        except MCPClientError:
            raise
        except MCPError as exc:
            logger.warning('Slides MCP failed to %s: %s', action, exc)
            raise MCPClientError(f'MCP server failed to {action}: {exc}') from exc
        except Exception as exc:
            logger.warning('Slides MCP failed to %s: %r', action, exc)
            raise MCPClientError(
                f'Lost connection to the Slides MCP server during {action}: '
                f'{_describe(exc)}'
            ) from exc


def _describe(exc):
    while isinstance(exc, BaseExceptionGroup) and len(exc.exceptions) == 1:
        exc = exc.exceptions[0]
    return str(exc) or type(exc).__name__
