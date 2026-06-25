import sys
import os
import json
import logging
from typing import Any, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .dependencies import ActorContext

logger = logging.getLogger(__name__)

# ── MCP Routines directory resolution ────────────────────────────────────────
# The MCP_ROUTINES_DIR environment variable takes precedence.
# This is set in the Dockerfile (ENV MCP_ROUTINES_DIR=/app/services/mcp-routines)
# so that the container does not rely on relative path derivation.
#
# Fallback (local development):
#   this file → services/agent-api/src/memorybridge_agent/mcp_client.py
#   three dirname() calls up → services/
#   + "mcp-routines" → services/mcp-routines
MCP_ROUTINES_DIR = os.environ.get("MCP_ROUTINES_DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "mcp-routines",
)

# ── Python executable resolution ──────────────────────────────────────────────
# In the Docker container, all packages are installed in the system site-packages.
# Prefer a venv if it exists (local development); otherwise use sys.executable
# (the same Python interpreter running the FastAPI process).
_venv_python = os.path.join(MCP_ROUTINES_DIR, "venv", "bin", "python")
MCP_PYTHON = _venv_python if os.path.isfile(_venv_python) else sys.executable


async def call_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    context: ActorContext
) -> Any:
    """
    Calls an MCP tool on the mcp-routines server securely via stdio.
    Transparently injects the `_context` with the trusted ActorContext.
    
    The MCP server process is started fresh for each tool call and exits
    when the async context manager exits.  No network port is used.
    """
    # Inject trusted context
    arguments["_context"] = context.model_dump()

    server_params = StdioServerParameters(
        command=MCP_PYTHON,
        args=["-m", "src.server"],
        env={
            **os.environ,  # Inherit DATABASE_URL and other env vars
            "PYTHONPATH": MCP_ROUTINES_DIR,
        },
    )

    logger.info(
        "Invoking MCP tool",
        extra={
            "tool_name": tool_name,
            "correlation_id": context.correlation_id,
            "actor_id": context.actor_id,
        },
    )

    # We must run from the mcp-routines directory so relative imports work.
    # Change directory temporarily; restore on exit.
    original_cwd = os.getcwd()
    try:
        os.chdir(MCP_ROUTINES_DIR)

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Execute the tool
                result = await session.call_tool(tool_name, arguments)

                # Unpack CallToolResult
                if getattr(result, "isError", False):
                    error_msg = result.content[0].text if result.content else "Unknown MCP error"
                    raise RuntimeError(f"MCP tool error: {error_msg}")

                if result.content and len(result.content) > 0:
                    text_content = result.content[0].text
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        return text_content
                return {}
    except Exception as exc:
        logger.error(f"MCP Tool invocation failed for tool={tool_name!r}: {exc}", exc_info=True)
        raise
    finally:
        os.chdir(original_cwd)
