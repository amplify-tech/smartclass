"""SmartClass Google Slides MCP server.

Run from the ``backend`` directory:

    python -m slides_mcp.server                              # stdio
    python -m slides_mcp.server --transport streamable-http  # http://127.0.0.1:8001/mcp
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from mcp.server import MCPServer

from slides_mcp import tools

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

mcp = MCPServer(
    'SmartClass Google Slides',
    instructions='Tools for working with Google Slides presentations.',
)

mcp.add_tool(tools.ping)
mcp.add_tool(tools.create_presentation)
mcp.add_tool(tools.get_presentation)
mcp.add_tool(tools.delete_presentation)
mcp.add_tool(tools.add_slide)
mcp.add_tool(tools.update_slide)
mcp.add_tool(tools.delete_slide)
mcp.add_tool(tools.add_text)
mcp.add_tool(tools.add_image)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        '--transport',
        choices=('stdio', 'streamable-http'),
        default='stdio',
    )
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()

    if args.transport == 'stdio':
        mcp.run()
    else:
        mcp.run(transport='streamable-http', host=args.host, port=args.port)


if __name__ == '__main__':
    main()
