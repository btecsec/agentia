"""myTravel's weather and risk tools, for other agents: MCP.

myTravel's own agents do not need this file: they call these
Python functions directly, in the same process. MCP is for the
agents we did not write (Claude Code, Claude Desktop, an IDE,
another team's agent, in any language): they connect here, ask
which tools exist, and call them.

    python mcp_server.py    # then http://127.0.0.1:8001/mcp
"""

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from app.tools import travel_advice, weather

load_dotenv()  # the same .env as the app: TAVILY_API_KEY

server = MCPServer("mytravel")
# The same functions as the agents use: one code, two doors. The
# name, the docstring and the typed arguments become the tool
# description any MCP client reads.
server.add_tool(weather.func)
server.add_tool(travel_advice.func)

if __name__ == "__main__":
    # HTTP rather than stdio: in stdio, standard output belongs to
    # the protocol, and the JSON logs of chapter 17 would break it.
    # 127.0.0.1 only: nobody else on the network can call it.
    server.run("streamable-http", port=8001)
