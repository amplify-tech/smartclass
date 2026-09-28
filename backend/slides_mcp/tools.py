"""MCP tool functions for the Google Slides MCP server.

Tools stay thin: they validate MCP inputs and delegate Google Slides API
work to ``google_integration.services``.
"""


def ping() -> str:
    """Check that the SmartClass Google Slides MCP server is reachable."""
    return 'pong'
