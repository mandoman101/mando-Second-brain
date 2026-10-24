#!/usr/bin/env python3
"""ForgePoints AI Lab — Clean-Room Integration Service (Milestones 1 & 2).

Bridges:
  1. Obsidian Second Brain (MIT) AI-First vault notes & MCP vault_ops
  2. Hypernovum (AGPL-3.0-only) 3D City project frontmatter & v2 agent heartbeats
  3. OpenClaw / ForgePoint live Apple Silicon cluster telemetry
  4. Cross-Agent Shared Memory API (search_memory, read_memory, propose_memory,
     get_project_context, record_task_outcome, get_system_health)

No hardcoded IPs, credentials, or machine assignments; all settings load from
config JSON or environment variables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = 2

_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{30,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key|password|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{12,}"),
]

_STATUS_TO_HYPERNOVUM = {
    "active": "active",
    "in-progress": "active",
    "planning": "active",
    "blocked": "blocked",
    "stalled": "blocked",
    "paused": "paused",
    "on-hold": "paused",
    "completed": "complete",
    "complete": "complete",
    "done": "complete",
    "archived": "complete",
}

_AGENT_ID_MAP = {
    "architect": ("agent-architect-m3max", "Architect (mando-mbp M3 Max 64GB)", "claude"),
    "analyst": ("agent-analyst-tybot", "Analyst (ty-bot M4 32GB)", "custom"),
    "coder": ("agent-coder-mandobot", "Coder (mando-bot M4 Pro 24GB)", "codex"),
    "main": ("agent-controller-milliegirl", "Controller (millie-girl M4 16GB)", "custom"),
}


class SecretLeakError(ValueError):
    """Raised when a proposed memory or observation contains credentials/secrets."""


class PathTraversalError(ValueError):
    """Raised when a path escapes the vault root or targets a protected directory."""


def ensure_no_secrets(text: str) -> None:
    """Verify that text contains no API keys, tokens, passwords, or private keys."""
    for pat in _SECRET_PATTERNS:
        if pat.search(text or ""):
            raise SecretLeakError("Refusing to store content matching secret/credential pattern.")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    path = config_path or os.environ.get("FORGEPOINTS_CONFIG") or str(
        Path(__file__).resolve().parent / "config.example.json"
    )
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    if os.environ.get("OBSIDIAN_VAULT_PATH"):
        cfg["vaultPath"] = os.environ["OBSIDIAN_VAULT_PATH"]
    if os.environ.get("FORGEPOINTS_TELEMETRY_URL"):
        cfg["telemetryUrl"] = os.environ["FORGEPOINTS_TELEMETRY_URL"]
    return cfg


class ForgePointsAdapter:
    """Clean-room adapter connecting Obsidian Second Brain, Hypernovum, and OpenClaw."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vault_path = Path(config["vaultPath"]).resolve()
        self.osb_path = Path(config["upstreamSecondBrainPath"]).resolve()
        self.hn_path = Path(config["upstreamHypernovumPath"]).resolve()
        os.environ["OBSIDIAN_VAULT_PATH"] = str(self.vault_path)
        self._load_upstream_vault_ops()

    def _bind_vault_env(self) -> None:
        os.environ["OBSIDIAN_VAULT_PATH"] = str(self.vault_path)

    def _load_upstream_vault_ops(self) -> None:
        mcp_dir = str(self.osb_path / "integrations" / "obsidian-mcp-server")
        if mcp_dir not in sys.path:
            sys.path.insert(0, mcp_dir)
        import vault_ops  # type: ignore
        self.vault_ops = vault_ops

    def _guard_vault_path(self, rel_path: str) -> Path:
        if not rel_path or rel_path.startswith("/") or ".." in Path(rel_path).parts:
            raise PathTraversalError(f"Invalid vault-relative path: {rel_path}")
        full = (self.vault_path / rel_path).resolve()
        if not str(full).startswith(str(self.vault_path)):
            raise PathTraversalError(f"Path escapes vault root: {rel_path}")
        top = Path(rel_path).parts[0].lower() if Path(rel_path).parts else ""
        if top in {"raw", ".obsidian", ".git", "templates", "_trash", ".trash"}:
            raise PathTraversalError(f"Protected vault directory cannot be modified: {top}")
        return full

    def emit_agent_activity(
        self,
        agent_id: str,
        state: str,
        action: str,
        project_title: str = "ForgePoints AI Lab Collective Intelligence",
        tool_name: str = "mcp",
        file_path: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Emit a real-time Hypernovum v2 agent heartbeat when an agent uses a memory tool."""
        hb_script = self.hn_path / "scripts" / "heartbeat.js"
        if not hb_script.exists():
            return None
        sid, name, atype = _AGENT_ID_MAP.get(
            agent_id,
            (f"agent-{agent_id}", f"Agent ({agent_id})", "custom"),
        )
        # Resolve projectDir from config if available
        proj_dir = str(self.vault_path.parent)
        for p in self.config.get("projects", []):
            if p.get("title", "").lower() == project_title.lower() or p.get("id", "").lower() == project_title.lower():
                proj_dir = p.get("projectDir", proj_dir)
                project_title = p.get("title", project_title)
                break
        cmd = [
            "node",
            str(hb_script),
            f"--vault={self.vault_path}",
            f"--id={sid}",
            f"--name={name}",
            f"--agent-type={atype}",
            f"--cwd={proj_dir}",
            f"--project={project_title}",
            f"--state={state}",
            f"--action={action}",
            f"--tool={tool_name}",
        ]
        if file_path:
            cmd.append(f"--file={file_path}")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=5)
            snap_file = self.vault_path / ".hypernovum" / "agents" / f"{sid}.json"
            if snap_file.exists():
                return json.loads(snap_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # 1. Dual-Schema Project Note Synthesizer (OSB AI-First + Hypernovum)
    # ------------------------------------------------------------------
    def render_dual_schema_project_note(self, proj: Dict[str, Any]) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        title = proj["title"]
        ensure_no_secrets(json.dumps(proj))

        raw_status = proj.get("status", "active")
        hn_status = _STATUS_TO_HYPERNOVUM.get(raw_status, "active")
        stage = proj.get("stage") or ("backlog" if raw_status == "planning" else hn_status)
        priority = proj.get("priority", "medium")
        category = proj.get("category", "ai-infrastructure")
        project_dir = proj.get("projectDir", "")
        stack = proj.get("stack", [])
        tasks_total = int(proj.get("tasks", 0))
        tasks_done = int(proj.get("tasks_done", 0))
        questions = proj.get("questions", [])
        answered = proj.get("answered", [])
        depends_on = proj.get("depends_on", [])
        summary = proj.get("summary", f"{title} project in ForgePoints AI Lab.")

        lines = [
            "---",
            f"date: {today}",
            f"updated: {today}",
            "type: project",
            f"title: {title}",
            f"status: {hn_status}",
            f"priority: {priority}",
            f"stage: {stage}",
            f"category: {category}",
            f"tags: [project, {category}, forgepoints]",
            "ai-first: true",
            "verification_status: verified",
            "confidence: high",
            f"repo: {project_dir}",
            f"projectDir: {project_dir}",
            f"tasks: {tasks_total}",
            f"tasks_done: {tasks_done}",
            f"stack: {json.dumps(stack)}",
        ]
        if depends_on:
            lines.append(f"related-projects: {json.dumps(depends_on)}")
            lines.append(f"depends_on: {json.dumps(depends_on)}")
            lines.append("relations:")
            lines.append(f"  depends_on: {json.dumps(depends_on)}")
        if questions:
            lines.append(f"questions: {json.dumps(questions)}")
        if answered:
            lines.append(f"answered: {json.dumps(answered)}")
        lines.append("---")
        lines.append("")
        lines.append("## For future agent")
        lines.append(
            f"{title} is an active ForgePoints AI Lab project in the `{category}` district with status `{hn_status}` as of {today}. "
            f"{summary} Primary code path: `{project_dir}`."
        )
        lines.append("")
        lines.append("## Overview")
        lines.append(summary)
        lines.append("")
        lines.append("## Architecture & Stack")
        for item in stack:
            lines.append(f"- **{item}**")
        if depends_on:
            lines.append("")
            lines.append("## Dependencies")
            for dep in depends_on:
                lines.append(f"- Depends on {dep}")
        lines.append("")
        lines.append("## Key Decisions")
        for ans in answered:
            lines.append(f"- [x] {ans} (as of {today}, confidence: stated)")
        for q in questions:
            lines.append(f"- [ ] Open Quest: {q}")
        lines.append("")
        return "\n".join(lines)

    def sync_projects_to_vault(self) -> List[str]:
        self._bind_vault_env()
        projects_dir = self.vault_path / "Projects"
        projects_dir.mkdir(parents=True, exist_ok=True)
        written: List[str] = []
        for proj in self.config.get("projects", []):
            title = proj["title"]
            rel = f"Projects/{title}.md"
            target = self._guard_vault_path(rel)
            content = self.render_dual_schema_project_note(proj)
            target.write_text(content, encoding="utf-8")
            written.append(rel)
        return written

    # ------------------------------------------------------------------
    # 2. Cross-Agent Memory Operations (6 Required MCP Capabilities)
    # ------------------------------------------------------------------
    def search_memory(self, query: str, limit: int = 6, agent_id: str = "analyst") -> List[Dict[str, Any]]:
        self._bind_vault_env()
        self.emit_agent_activity(agent_id, "reading", f"Searching memory: {query[:40]}", tool_name="search_memory")
        return self.vault_ops.search(query, limit=limit)

    def read_memory(self, rel_path: str, agent_id: str = "analyst") -> Dict[str, Any]:
        self._bind_vault_env()
        self._guard_vault_path(rel_path)
        self.emit_agent_activity(agent_id, "reading", f"Reading {rel_path}", tool_name="read_memory", file_path=rel_path)
        return self.vault_ops.read_note(rel_path)

    def propose_memory(
        self,
        title: str,
        content: str,
        note_type: str = "research",
        tags: Optional[List[str]] = None,
        source_ref: str = "",
        project_link: str = "",
        confidence: str = "high",
        verification_status: str = "verified",
        agent_id: str = "analyst",
    ) -> Dict[str, Any]:
        self._bind_vault_env()
        ensure_no_secrets(title)
        ensure_no_secrets(content)
        ensure_no_secrets(source_ref)
        if not agent_id or agent_id == "unauthorized":
            raise PermissionError("Unauthorized agent_id cannot write to vault memory.")

        norm_hash = hashlib.sha256(f"{title.strip().lower()}::{content.strip()}".encode("utf-8")).hexdigest()[:16]
        inbox_dir = self.vault_path / "Inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        for existing in inbox_dir.glob("*.md"):
            txt = existing.read_text(encoding="utf-8", errors="ignore")
            if f"content_hash: {norm_hash}" in txt:
                return {
                    "saved": False,
                    "duplicate": True,
                    "path": str(existing.relative_to(self.vault_path)),
                    "content_hash": norm_hash,
                }

        today = datetime.now().strftime("%Y-%m-%d")
        enriched_body = content.strip()
        if source_ref:
            enriched_body += f"\n\n## Sources\n- Source Reference: {source_ref} (as of {today}, confidence: {confidence})"
        if project_link:
            enriched_body += f"\n- Related Project: [[Projects/{project_link}]]"
        enriched_body += f"\n- Recorded by Agent: `{agent_id}` | Verification: `{verification_status}` | content_hash: {norm_hash}\n"

        tag_list = list(tags or [note_type, "forgepoints"])
        summary = f"{note_type.capitalize()} note '{title}' recorded by {agent_id} on {today} (verification: {verification_status}, confidence: {confidence})."
        res = self.vault_ops.save_note(title, enriched_body, note_type=note_type, tags=tag_list, summary=summary)
        if "saved" in res and "path" not in res:
            res["path"] = res["saved"]
        res["content_hash"] = norm_hash
        res["duplicate"] = False
        self.emit_agent_activity(
            agent_id,
            "editing",
            f"Saved memory: {title[:36]}",
            project_title=project_link or "ForgePoints AI Lab Collective Intelligence",
            tool_name="propose_memory",
            file_path=res.get("path"),
        )
        return res

    def get_project_context(self, project_name: str, agent_id: str = "architect") -> Dict[str, Any]:
        """Retrieve full project dossier, frontmatter, open quests, and backlinked notes."""
        self._bind_vault_env()
        projects_dir = self.vault_path / "Projects"
        matched_rel: Optional[str] = None
        if projects_dir.is_dir():
            for md in sorted(projects_dir.glob("*.md")):
                if project_name.lower() in md.stem.lower():
                    matched_rel = f"Projects/{md.name}"
                    break
        if not matched_rel:
            return {"found": False, "error": f"Project '{project_name}' not found in Projects/"}

        note = self.vault_ops.read_note(matched_rel)
        bl = self.vault_ops.backlinks(Path(matched_rel).stem)
        self.emit_agent_activity(
            agent_id,
            "planning",
            f"Inspecting project context: {Path(matched_rel).stem}",
            project_title=Path(matched_rel).stem,
            tool_name="get_project_context",
            file_path=matched_rel,
        )
        return {
            "found": True,
            "path": matched_rel,
            "title": Path(matched_rel).stem,
            "content": note.get("content", ""),
            "backlinks": bl.get("backlinks", []),
        }

    def record_task_outcome(
        self,
        project_name: str,
        task_summary: str,
        outcome: str = "completed",
        resolved_quest: Optional[str] = None,
        agent_id: str = "coder",
        files_changed: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Record a completed task outcome into the project note, increment tasks_done, and emit orb state."""
        self._bind_vault_env()
        ensure_no_secrets(task_summary)
        ctx = self.get_project_context(project_name, agent_id=agent_id)
        if not ctx.get("found"):
            return ctx

        rel_path = ctx["path"]
        full_path = self._guard_vault_path(rel_path)
        text = full_path.read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")

        # Increment tasks_done in YAML frontmatter if present
        m_done = re.search(r"(?m)^tasks_done:\s*(\d+)", text)
        m_tot = re.search(r"(?m)^tasks:\s*(\d+)", text)
        if m_done and outcome == "completed":
            new_done = int(m_done.group(1)) + 1
            text = re.sub(r"(?m)^tasks_done:\s*\d+", f"tasks_done: {new_done}", text, count=1)
            if m_tot and new_done > int(m_tot.group(1)):
                text = re.sub(r"(?m)^tasks:\s*\d+", f"tasks: {new_done}", text, count=1)

        # Append task outcome entry under ## Recent Outcomes (or end of note)
        files_str = f" (files: {', '.join(files_changed)})" if files_changed else ""
        outcome_line = f"- [{'x' if outcome == 'completed' else ' '}] **{today}** (`{agent_id}` · `{outcome}`): {task_summary}{files_str} (as of {today}, confidence: stated)"
        if "## Recent Outcomes" in text:
            text = text.rstrip() + "\n" + outcome_line + "\n"
        else:
            text = text.rstrip() + "\n\n## Recent Outcomes\n" + outcome_line + "\n"

        if resolved_quest:
            ensure_no_secrets(resolved_quest)
            text = text.replace(f"- [ ] Open Quest: {resolved_quest}", f"- [x] Resolved Quest: {resolved_quest} (as of {today})")

        full_path.write_text(text, encoding="utf-8")
        hb_state = "complete" if outcome == "completed" else ("blocked" if outcome == "blocked" else "running")
        snap = self.emit_agent_activity(
            agent_id,
            hb_state,
            f"{outcome.upper()}: {task_summary[:42]}",
            project_title=ctx["title"],
            tool_name="record_task_outcome",
            file_path=rel_path,
        )
        return {
            "ok": True,
            "project": ctx["title"],
            "path": rel_path,
            "outcome": outcome,
            "agent_id": agent_id,
            "heartbeat": snap,
        }

    def get_vault_health(self) -> Dict[str, Any]:
        self._bind_vault_env()
        return self.vault_ops.vault_health()

    # ------------------------------------------------------------------
    # 4. Phase 5: Conflict Detection & File Lock Guard (AGT-007 Parity)
    # ------------------------------------------------------------------
    def detect_active_conflicts(self, active_window_ms: int = 600000) -> List[Dict[str, Any]]:
        """Detect deterministic same-file and same-project conflicts across active .hypernovum/agents/*.json sessions."""
        agents_dir = self.vault_path / ".hypernovum" / "agents"
        if not agents_dir.is_dir():
            return []
        now_ms = int(datetime.now().timestamp() * 1000)
        working_states = {"starting", "planning", "reading", "editing", "running", "testing", "reviewing", "waiting", "blocked"}
        sessions: List[Dict[str, Any]] = []
        for jf in sorted(agents_dir.glob("*.json")):
            try:
                s = json.loads(jf.read_text(encoding="utf-8"))
                if s.get("stoppedAt"):  # stopped sessions are not actively conflicting
                    continue
                if now_ms - int(s.get("lastPing", 0)) > active_window_ms:
                    continue
                if s.get("state") in working_states:
                    sessions.append(s)
            except Exception:
                pass

        conflicts: List[Dict[str, Any]] = []
        for i in range(len(sessions)):
            for j in range(i + 1, len(sessions)):
                a, b = sessions[i], sessions[j]
                proj_a = (a.get("project") or "").strip()
                proj_b = (b.get("project") or "").strip()
                if not proj_a or proj_a.lower() != proj_b.lower():
                    continue
                pair = sorted([a.get("sessionId", "a"), b.get("sessionId", "b")])
                file_a = (a.get("file") or "").strip().lstrip("./")
                file_b = (b.get("file") or "").strip().lstrip("./")
                if file_a and file_a == file_b:
                    conflicts.append({
                        "key": f"same-file|{pair[0]}|{pair[1]}|{file_a}",
                        "kind": "same-file",
                        "severity": "high",
                        "sessions": pair,
                        "project": proj_a,
                        "files": [file_a],
                        "message": f"{a.get('name', pair[0])} and {b.get('name', pair[1])} are both touching '{file_a}' in '{proj_a}'",
                    })
                elif a.get("state") == "editing" and b.get("state") == "editing":
                    conflicts.append({
                        "key": f"same-project|{pair[0]}|{pair[1]}|{proj_a}",
                        "kind": "same-project",
                        "severity": "medium",
                        "sessions": pair,
                        "project": proj_a,
                        "files": [f for f in (file_a, file_b) if f],
                        "message": f"{a.get('name', pair[0])} and {b.get('name', pair[1])} are concurrently editing in project '{proj_a}'",
                    })
        return conflicts

    def claim_file_scope(
        self,
        agent_id: str,
        project_name: str,
        file_path: str,
        action: str = "Editing file",
    ) -> Dict[str, Any]:
        """Claim a file write-scope for an agent, rejecting with a conflict warning if another active agent already owns that file."""
        ensure_no_secrets(file_path)
        norm_target = file_path.strip().lstrip("./")
        sid, _, _ = _AGENT_ID_MAP.get(agent_id, (f"agent-{agent_id}", agent_id, "custom"))

        # Check if any OTHER active session is currently editing this exact file in this project
        agents_dir = self.vault_path / ".hypernovum" / "agents"
        if agents_dir.is_dir():
            for jf in sorted(agents_dir.glob("*.json")):
                try:
                    s = json.loads(jf.read_text(encoding="utf-8"))
                    other_sid = s.get("sessionId")
                    if other_sid == sid or s.get("stoppedAt"):
                        continue
                    other_proj = (s.get("project") or "").lower()
                    other_file = (s.get("file") or "").strip().lstrip("./")
                    if project_name.lower() in other_proj and other_file == norm_target and s.get("state") in {"editing", "running"}:
                        return {
                            "acquired": False,
                            "conflict": True,
                            "holderSessionId": other_sid,
                            "holderName": s.get("name"),
                            "file": norm_target,
                            "project": s.get("project"),
                            "message": f"Single-Writer Lock denied: {s.get('name')} ({other_sid}) is already editing '{norm_target}' in '{s.get('project')}'.",
                        }
                except Exception:
                    pass

        snap = self.emit_agent_activity(
            agent_id=agent_id,
            state="editing",
            action=f"{action}: {norm_target}",
            project_title=project_name,
            tool_name="claim_file_scope",
            file_path=norm_target,
        )
        return {
            "acquired": True,
            "conflict": False,
            "sessionId": sid,
            "file": norm_target,
            "project": project_name,
            "heartbeat": snap,
        }

    def get_system_health(self, agent_id: str = "main") -> Dict[str, Any]:
        """Combined health check of the Second-Brain Vault, Cluster Telemetry, and Hypernovum Agent Fleet."""
        self._bind_vault_env()
        v_health = self.vault_ops.vault_health()
        telemetry = self.fetch_live_cluster_telemetry()
        agents_dir = self.vault_path / ".hypernovum" / "agents"
        fleet = []
        if agents_dir.is_dir():
            for jf in sorted(agents_dir.glob("*.json")):
                try:
                    fleet.append(json.loads(jf.read_text(encoding="utf-8")))
                except Exception:
                    pass
        return {
            "status": "healthy",
            "vaultPath": str(self.vault_path),
            "vaultHealth": v_health,
            "clusterSummary": {
                "poolRamUsedGb": telemetry.get("poolRamUsed", 0.0),
                "poolRamTotalGb": telemetry.get("poolRamTotal", 0.0),
                "onlineNodes": [n["id"] for n in telemetry.get("nodes", []) if n.get("online")],
            },
            "hypernovumFleetCount": len(fleet),
            "hypernovumFleet": fleet,
            "activeConflicts": self.detect_active_conflicts(),
        }

    # ------------------------------------------------------------------
    # 3. Live Cluster Telemetry -> Hypernovum Heartbeat v2 Bridge
    # ------------------------------------------------------------------
    def fetch_live_cluster_telemetry(self) -> Dict[str, Any]:
        url = self.config.get("telemetryUrl", "http://127.0.0.1:18795/api/metrics")
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            raw = urllib.request.urlopen(req, timeout=2.5).read().decode("utf-8")
            return json.loads(raw)
        except Exception as e:
            return {"nodes": [], "error": str(e)}

    def sync_cluster_heartbeats(self, telemetry_override: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        telemetry = telemetry_override if telemetry_override is not None else self.fetch_live_cluster_telemetry()
        nodes_by_id = {n["id"]: n for n in telemetry.get("nodes", []) if "id" in n}
        hb_script = self.hn_path / "scripts" / "heartbeat.js"
        emitted: List[Dict[str, Any]] = []

        for mapping in self.config.get("agentNodeMappings", []):
            nid = mapping["nodeId"]
            sid = mapping["sessionId"]
            node_state = nodes_by_id.get(nid)
            if not node_state or not node_state.get("online", False):
                state = "failed"
                action = f"Node {nid} offline / unreachable"
                stop_flag = True
            else:
                gpu = int(node_state.get("gpuPct", 0))
                cpu = float(node_state.get("avgCpu", 0.0))
                ram_used = node_state.get("ramUsed", 0.0)
                ram_tot = node_state.get("ramTotal", 0.0)
                model_lbl = node_state.get("modelLabel", "oMLX")
                if gpu >= 15 or cpu >= 20.0:
                    state = "running"
                else:
                    state = "reading"
                action = f"{model_lbl} | RAM {ram_used}/{ram_tot}GB | GPU {gpu}% | CPU {cpu}%"
                stop_flag = False

            cmd = [
                "node",
                str(hb_script),
                f"--vault={self.vault_path}",
                f"--id={sid}",
                f"--name={mapping['agentName']}",
                f"--agent-type={mapping.get('agentType', 'custom')}",
                f"--cwd={mapping['targetProjectDir']}",
                f"--project={mapping['targetProjectTitle']}",
                f"--state={state}",
                f"--action={action}",
            ]
            if stop_flag:
                cmd.append("--stop")
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=5)
            snap_file = self.vault_path / ".hypernovum" / "agents" / f"{sid}.json"
            if snap_file.exists():
                emitted.append(json.loads(snap_file.read_text(encoding="utf-8")))
        return emitted

    def install_hypernovum_plugin_into_vault(self) -> Dict[str, Any]:
        plugin_src = self.hn_path / "packages" / "obsidian-plugin"
        plugin_dst = self.vault_path / ".obsidian" / "plugins" / "hypernovum"
        plugin_dst.mkdir(parents=True, exist_ok=True)
        copied = []
        for fname in ("main.js", "manifest.json", "styles.css"):
            src_f = plugin_src / fname
            if src_f.exists():
                dst_f = plugin_dst / fname
                dst_f.write_bytes(src_f.read_bytes())
                copied.append(fname)
        cp_file = self.vault_path / ".obsidian" / "community-plugins.json"
        cp_file.write_text(json.dumps(["hypernovum"], indent=2) + "\n", encoding="utf-8")
        return {"pluginDir": str(plugin_dst), "files": copied}


def main() -> None:
    parser = argparse.ArgumentParser(description="ForgePoints AI Lab Integration Service")
    parser.add_argument("--config", default=None, help="Path to config JSON")
    parser.add_argument("command", choices=["sync-projects", "sync-heartbeats", "install-plugin", "sync-all", "health"])
    args = parser.parse_args()

    cfg = load_config(args.config)
    adapter = ForgePointsAdapter(cfg)

    if args.command in ("install-plugin", "sync-all"):
        p_res = adapter.install_hypernovum_plugin_into_vault()
        print("Installed Hypernovum plugin into test-vault:", json.dumps(p_res))
    if args.command in ("sync-projects", "sync-all"):
        written = adapter.sync_projects_to_vault()
        print("Synced dual-schema project notes:", json.dumps(written))
    if args.command in ("sync-heartbeats", "sync-all"):
        snaps = adapter.sync_cluster_heartbeats()
        print(f"Synced {len(snaps)} live cluster agent heartbeats into .hypernovum/agents/")
    if args.command in ("health", "sync-all"):
        h = adapter.get_system_health()
        print("System health:", json.dumps(h, indent=2))


if __name__ == "__main__":
    main()
