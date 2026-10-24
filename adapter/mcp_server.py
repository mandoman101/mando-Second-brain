#!/usr/bin/env python3
"""ForgePoints AI Lab — Shared Agent Memory MCP Server (Milestone 2).

Exposes the 6 Phase 4 Collective Intelligence capabilities over stdio MCP:
  1. search_memory(query, limit, agent_id)
  2. read_memory(rel_path, agent_id)
  3. propose_memory(title, content, note_type, tags, source_ref, project_link, confidence, verification_status, agent_id)
  4. get_project_context(project_name, agent_id)
  5. record_task_outcome(project_name, task_summary, outcome, resolved_quest, agent_id, files_changed)
  6. get_system_health(agent_id)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

ADAPTER_DIR = Path(__file__).resolve().parent
if str(ADAPTER_DIR) not in sys.path:
    sys.path.insert(0, str(ADAPTER_DIR))

from forgepoints_adapter import ForgePointsAdapter, load_config  # noqa: E402

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        class FastMCP:
            def __init__(self, name: str):
                self.name = name
            def tool(self):
                def _decorator(fn):
                    return fn
                return _decorator
            def run(self):
                raise RuntimeError('mcp package is required to run stdio server')

mcp = FastMCP("forgepoints-memory-mcp")


def _adapter() -> ForgePointsAdapter:
    return ForgePointsAdapter(load_config())


@mcp.tool()
def search_memory(query: str, limit: int = 6, agent_id: str = "analyst") -> str:
    """Search the shared ForgePoints Second-Brain vault and emit a reading heartbeat to the 3D City."""
    res = _adapter().search_memory(query=query, limit=limit, agent_id=agent_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def read_memory(rel_path: str, agent_id: str = "analyst") -> str:
    """Read a note by vault-relative path (path-traversal guarded) and emit a reading heartbeat."""
    res = _adapter().read_memory(rel_path=rel_path, agent_id=agent_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def propose_memory(
    title: str,
    content: str,
    note_type: str = "research",
    tags: Optional[List[str]] = None,
    source_ref: str = "",
    project_link: str = "",
    confidence: str = "high",
    verification_status: str = "verified",
    agent_id: str = "analyst",
) -> str:
    """Propose and save a secret-scrubbed, deduplicated, source-cited AI-First memory note into Inbox/."""
    res = _adapter().propose_memory(
        title=title,
        content=content,
        note_type=note_type,
        tags=tags,
        source_ref=source_ref,
        project_link=project_link,
        confidence=confidence,
        verification_status=verification_status,
        agent_id=agent_id,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def get_project_context(project_name: str, agent_id: str = "architect") -> str:
    """Retrieve the dual-schema project dossier, frontmatter, open quests, and backlinks for a project."""
    res = _adapter().get_project_context(project_name=project_name, agent_id=agent_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def record_task_outcome(
    project_name: str,
    task_summary: str,
    outcome: str = "completed",
    resolved_quest: Optional[str] = None,
    agent_id: str = "coder",
    files_changed: Optional[List[str]] = None,
) -> str:
    """Record a completed or blocked task outcome onto a project note, update lit building windows, and update the 3D agent orb."""
    res = _adapter().record_task_outcome(
        project_name=project_name,
        task_summary=task_summary,
        outcome=outcome,
        resolved_quest=resolved_quest,
        agent_id=agent_id,
        files_changed=files_changed,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def get_system_health(agent_id: str = "main") -> str:
    """Return combined health of the Second-Brain Vault, Apple Silicon Cluster Telemetry, and Hypernovum 3D Agent Fleet."""
    res = _adapter().get_system_health(agent_id=agent_id)
    return json.dumps(res, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
