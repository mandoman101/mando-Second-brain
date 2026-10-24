# Integration Guide: Obsidian Second Brain + Hypernovum + OpenClaw

## How Dual-Schema Project Notes Work
When `forgepoints_adapter.py` creates or normalizes a project note in `Projects/<Name>.md`, it writes:
1. **Obsidian Second Brain AI-First fields:** `date`, `updated`, `type: project`, `tags: [project, ...]`, `ai-first: true`, `repo`, `related-projects`, `relations.depends_on`, and the mandatory `## For future agent` preamble.
2. **Hypernovum 3D City fields:** `title`, `status` (`active|blocked|paused|complete`), `priority` (`critical|high|medium|low`), `stage`, `category` (district), `projectDir`, `stack`, `depends_on`, `blocked_by`, `questions` (floating quest gems), and `tasks`/`tasks_done` (lit building windows).

## How Live Cluster Activity Reaches the 3D City
- `forgepoints_adapter.py sync-heartbeats` queries the configured cluster telemetry endpoint (or node probes) and invokes Hypernovum's atomic v2 snapshot protocol (`<vault>/.hypernovum/agents/<nodeId>.json`).
- When an agent node (`ty-bot`, `mando-bot`, `mando-mbp`) is actively generating tokens or running tools, its orb state transitions to `running`/`editing`/`reading` on its assigned project building; when idle or offline, it transitions accurately to `complete` or `failed`.
