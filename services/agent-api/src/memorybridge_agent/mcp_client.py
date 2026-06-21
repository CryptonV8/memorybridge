import sys
import os
import json
import logging
from typing import Any, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from .dependencies import ActorContext

logger = logging.getLogger(__name__)

# Derive the path to mcp-routines relative to this file
# Assuming this file is at services/agent-api/src/memorybridge_agent/mcp_client.py
# The mcp-routines folder is at services/mcp-routines
AGENT_API_SRC = os.path.dirname(os.path.abspath(__file__))
AGENT_API_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(AGENT_API_SRC)))
MCP_ROUTINES_DIR = os.path.join(AGENT_API_ROOT, "mcp-routines")

async def call_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    context: ActorContext
) -> Any:
    """
    Calls an MCP tool on the mcp-routines server securely via stdio.
    Transparently injects the `_context` with the trusted ActorContext.
    """
    # Inject trusted context
    arguments["_context"] = context.model_dump()
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.server"], # Assuming src.server is the entry point
        env={"PYTHONPATH": "."}, # Ensuring imports work
        # Setting CWD for the server process to the mcp-routines directory
    )
    
    # We must explicitly set the working directory for the mcp-routines execution.
    # Actually mcp.client.stdio.stdio_client doesn't natively expose cwd parameter in StdioServerParameters in some versions.
    # We will temporarily change cwd or handle it by setting PYTHONPATH.
    
    logger.info(f"Invoking MCP tool {tool_name} with context ID {context.correlation_id}")
    
    # Let's run it from the mcp-routines directory
    original_cwd = os.getcwd()
    try:
        os.chdir(MCP_ROUTINES_DIR)
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Execute the tool
                result = await session.call_tool(tool_name, arguments)
                return result
    except Exception as exc:
        logger.error(f"MCP Tool invocation failed: {exc}", exc_info=True)
        raise
    finally:
        os.chdir(original_cwd)
