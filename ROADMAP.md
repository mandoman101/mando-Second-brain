# ForgePoints AI Lab — Phased Engineering Roadmap

All 7 phases of the Master Project Specification are **COMPLETE** and verified by our 20-test automated suite (`pytest`).

- **Phase 1: Assessment & Reconnaissance (COMPLETED 2026-10-24)**
  - Cloned and audited `obsidian-second-brain` (`v0.19.0`, MIT) and `hypernovum` (`v0.7.0`, AGPL-3.0-only).
  - Identified Python `>=3.10` runtime requirement for OSB scripts and mapped the 4 frontmatter differences between OSB AI-first rules and Hypernovum `SCHEMA.md`.
- **Phase 2: Safe Development Environment (COMPLETED 2026-10-24)**
  - Created `/Users/millie-girl/development/forgepoints-ai-lab` with isolated `upstream/`, `test-vault/`, `adapter/`, and `tests/`.
  - Verified 22/22 `obsidian-second-brain` MCP tests and 370/370 `hypernovum` Vitest tests.
  - Bootstrapped `test-vault/` and installed the compiled `@hypernovum/obsidian` plugin (`main.js`, `manifest.json`, `styles.css`) into `test-vault/.obsidian/plugins/hypernovum/`.
- **Phase 3: First End-to-End Integration — Milestone 1 (COMPLETED 2026-10-24)**
  - Implemented `adapter/forgepoints_adapter.py` bridging AI-First project notes, cross-agent memory operations (with secret scrubbing & path traversal protection), and live cluster telemetry into Hypernovum `.hypernovum/agents/*.json` v2 heartbeat snapshots.
  - Verified with 8 automated unit & integration tests (`tests/test_forgepoints_milestone1.py`).
- **Phase 4: Shared Agent Memory via OpenClaw MCP — Milestone 2 (COMPLETED 2026-10-24)**
  - Implemented `adapter/mcp_server.py` and registered `forgepoints-memory-mcp` in OpenClaw on `millie-girl` (`.101`).
  - Verified live 3-node collective memory round-trip across `analyst` (`.103`), `architect` (`.158`), and `coder` (`.102`) (`tests/test_forgepoints_milestone2.py`).
- **Phase 5: Live Operational Visibility & Conflict Guard — Milestone 3 (COMPLETED 2026-10-24)**
  - Implemented deterministic same-file and same-project conflict detection (`detect_active_conflicts`) and single-writer file lock enforcement (`claim_file_scope`) matching Hypernovum `ConflictDetector.ts` (`AGT-007`) and Article IV of `AGENT_CONSTITUTION.md`.
  - Wired continuous background heartbeat synchronization into `ensure-ai-cluster.sh` on `.101` (`tests/test_forgepoints_milestone3.py`).
- **Phase 6: Memory Curation, Graduation & Non-Destructive Superseding — Milestone 4 (COMPLETED 2026-10-24)**
  - Implemented `graduate_memory` (promoting verified `Inbox/` captures to `Knowledge/` with non-destructive redirect stubs), `supersede_memory` (stamping `status: superseded` and bidirectional `supersedes`/`superseded_by` links without deleting history), and `audit_memory_freshness`.
- **Phase 7: Local SQLite FTS5 + TF-IDF Vector Hybrid Search Index — Milestone 4 (COMPLETED 2026-10-24)**
  - Implemented `rebuild_search_index` and `hybrid_search_memory` backed by `<vault>/.forgepoints/memory_index.sqlite3` combining SQLite FTS5 `bm25()` lexical ranking with normalized TF-IDF cosine vector similarity, verification boosting (`1.25x`), and superseded note demotion (`0.35x`) (`tests/test_forgepoints_milestone4.py`).
