# ForgePoints AI Lab — Phased Engineering Roadmap

- **Phase 1: Assessment & Reconnaissance (COMPLETED 2026-10-24)**
  - Cloned and audited `obsidian-second-brain` (`v0.19.0`) and `hypernovum` (`v0.7.0`).
  - Identified Python `>=3.10` runtime requirement for OSB scripts and mapped the 4 frontmatter differences between OSB AI-first rules and Hypernovum `SCHEMA.md`.
- **Phase 2: Safe Development Environment (COMPLETED 2026-10-24)**
  - Created `/Users/millie-girl/development/forgepoints-ai-lab` with isolated `upstream/`, `test-vault/`, `adapter/`, and `tests/`.
  - Verified 22/22 `obsidian-second-brain` MCP tests and 370/370 `hypernovum` Vitest tests.
  - Bootstrapped `test-vault/` and installed the compiled `@hypernovum/obsidian` plugin (`main.js`, `manifest.json`, `styles.css`) into `test-vault/.obsidian/plugins/hypernovum/`.
- **Phase 3: First End-to-End Integration — Milestone 1 (COMPLETED 2026-10-24)**
  - Implemented `adapter/forgepoints_adapter.py` bridging AI-First project notes, cross-agent memory operations (with secret scrubbing & path traversal protection), and live cluster telemetry into Hypernovum `.hypernovum/agents/*.json` v2 heartbeat snapshots.
  - Verified with 12 automated unit & integration tests (`tests/test_forgepoints_milestone1.py`).
- **Phase 4: Shared Agent Memory via OpenClaw MCP (NEXT MILESTONE)**
  - Register `obsidian-second-brain` MCP server + `forgepoints_adapter` in OpenClaw on `millie-girl` (`.101`) pointing at the target vault.
  - Verify `analyst` (`.103`), `architect` (`.158`), and `coder` (`.102`) retrieving verified memories and proposing source-backed notes.
- **Phase 5: Live Operational Visibility & Conflict Rings**
  - Wire OpenClaw sub-agent lifecycle hooks to emit real-time `.hypernovum/agents/<runId>.json` heartbeats during `analyst`/`coder` tool execution.
- **Phase 6 & 7: Quality Refinement & Optional Local Semantic Search**
