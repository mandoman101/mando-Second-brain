# Licenses, Attribution & Upstream Strategy

## 1. Upstream License Inventory

| Component | Upstream Repository | Author / Copyright | License | Verified License File |
| :--- | :--- | :--- | :--- | :--- |
| **Obsidian Second Brain** | `https://github.com/eugeniughelbur/obsidian-second-brain` | Copyright (c) 2026 Eugeniu Ghelbur | **MIT License** | `upstream/obsidian-second-brain/LICENSE` |
| **Hypernovum** (`@hypernovum/core`, `@hypernovum/obsidian`) | `https://github.com/Pardesco/hypernovum` | Copyright (c) 2026 Randall Morgan | **GNU Affero General Public License v3.0 only (`AGPL-3.0-only`)** | `upstream/hypernovum/LICENSE` |
| **Vendored Obsidian Skills inside Hypernovum** | `packages/obsidian-plugin/src/generated/obsidianSkills.ts` | Kepano / Obsidian Skills contributors | **MIT License** | `upstream/hypernovum/docs/OBSIDIAN-SKILLS-LICENSE.txt` |

## 2. Legal & Architectural Separation Strategy

1. **Strict Repository & Source-Tree Separation:**
   - `upstream/obsidian-second-brain/` (`MIT`) and `upstream/hypernovum/` (`AGPL-3.0-only`) are kept in separate, unmodified upstream directories with their original `LICENSE` files intact.
   - We **never** copy AGPL-3.0 code from `hypernovum` into `obsidian-second-brain` or into `adapter/`.
2. **File-Format & Protocol Interoperability:**
   - `ForgePoints Integration Service` (`adapter/forgepoints_adapter.py`) communicates with both systems exclusively through **documented open data formats on disk** inside the user's Obsidian vault:
     - Standard Markdown files with YAML frontmatter (`Projects/*.md`) as documented in `SCHEMA.md` and `references/ai-first-rules.md`.
     - Standard JSON session snapshots (`.hypernovum/agents/<sessionId>.json`) via the documented CLI contract of `heartbeat.js`.
3. **Distribution & AGPL-3.0 Implications:**
   - For local/private operation across Millie's Apple Silicon cluster, running unmodified `hypernovum` inside Obsidian and interacting via vault files triggers no network redistribution obligations.
   - If Millie ever distributes a modified version of `hypernovum` (or hosts `hypernovum` over a network for external users), **AGPL-3.0 Section 13** requires making the complete corresponding source code of the `hypernovum` work available under `AGPL-3.0`. Keeping `adapter/` and `obsidian-second-brain` decoupled as standalone vault-file producers preserves clean boundaries.
