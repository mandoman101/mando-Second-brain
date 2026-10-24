# ForgePoints AI Lab — Collective Intelligence
**Developed under MANDO–MAN Software**

A local-first, multi-agent collective intelligence environment and 3D operational command center designed for Apple Silicon clusters. ForgePoints AI Lab bridges two open-source foundations without conflating their source trees or violating their licenses:

1. **Component A — Persistent Knowledge Layer:** [Obsidian Second Brain](https://github.com/eugeniughelbur/obsidian-second-brain) (`v0.19.0`, `MIT` License)
2. **Component B — 3D Visual Command Center:** [Hypernovum](https://github.com/Pardesco/hypernovum) (`v0.7.0`, `AGPL-3.0-only` License)
3. **Component C — ForgePoints Integration Service (`adapter/`):** Clean-room Python & Node integration layer normalizing unified AI-First + Hypernovum project schemas, cross-agent memory operations (with secret-scrubbing & path guards), and live Apple Silicon cluster heartbeat projection.

## Workspace Layout (`/Users/millie-girl/development/forgepoints-ai-lab`)
- `upstream/obsidian-second-brain/` — Unmodified upstream clone (`MIT`, commit-pinned, 22/22 MCP tests passing).
- `upstream/hypernovum/` — Unmodified upstream clone (`AGPL-3.0-only`, commit-pinned, 43 test files / 370 tests passing, `@hypernovum/core` + `@hypernovum/obsidian` built).
- `test-vault/` — Isolated test Obsidian vault bootstrapped via `bootstrap_vault.py` (`--preset builder --style obsidian`) with `.obsidian/plugins/hypernovum/` installed and dual-schema project notes.
- `adapter/` — Clean-room ForgePoints Integration Service (`forgepoints_adapter.py`, `config.example.json`) implementing unified frontmatter synthesis, secret-guarded memory API, and live cluster-to-`.hypernovum/agents/*.json` heartbeat bridging.
- `tests/` — Automated unit and integration test suite (`test_forgepoints_milestone1.py`).

## Quick Start (macOS Apple Silicon)
```bash
cd /Users/millie-girl/development/forgepoints-ai-lab
# 1. Run the Milestone 1 test suite (12 unit & integration tests)
/opt/homebrew/bin/uv run --directory upstream/obsidian-second-brain pytest ../../tests/test_forgepoints_milestone1.py

# 2. Sync live cluster nodes & project notes into test-vault/.hypernovum/agents/
python3 adapter/forgepoints_adapter.py --config adapter/config.example.json sync-all
```
