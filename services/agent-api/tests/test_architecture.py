import os
import pytest
from pathlib import Path

def test_no_database_imports():
    """
    Architectural boundary test:
    Ensures that the agent-api service does not contain any direct imports
    to the database or models of the mcp-routines service.
    """
    agent_api_dir = Path(__file__).parent.parent / "src" / "memorybridge_agent"
    
    forbidden_strings = [
        "import src.models",
        "from src.models",
        "import src.database",
        "from src.database",
        "from ..mcp-routines",
        "import sqlalchemy"
    ]
    
    violations = []
    
    for root, _, files in os.walk(agent_api_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                content = file_path.read_text(encoding="utf-8")
                
                for forbidden in forbidden_strings:
                    if forbidden in content:
                        violations.append(f"{file_path.name} contains forbidden import: {forbidden}")
                        
    assert not violations, "Architectural boundary violation found: \n" + "\n".join(violations)
