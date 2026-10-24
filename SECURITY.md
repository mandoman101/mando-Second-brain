# Security & Reliability Architecture

1. **Local-First & Zero Unauthenticated LAN Writes:**
   - All vault mutations happen locally on filesystem paths validated against `vault_root`.
2. **Path Traversal Prevention:**
   - `forgepoints_adapter.py` and `vault_ops.py` resolve all note paths via `Path.resolve()` and reject any path escaping `vault_root` or targeting protected directories (`raw/`, `.obsidian/`, `.git/`, `Templates/`).
3. **Automatic Secret Exclusion Gate (`redact_or_reject_secrets`):**
   - Before any memory or observation is written to the vault, `forgepoints_adapter.py` scans for API keys, Bearer tokens, private keys (`-----BEGIN ... PRIVATE KEY-----`), `sk-...`, `ghp_...`, and password assignments. Any payload containing credentials is rejected with `SecretLeakError` so secrets never enter Markdown notes or operation logs.
4. **Untrusted Content Isolation:**
   - External research captures land in immutable `raw/` with `source_quality` and `capture_scope` metadata and are never executed as agent instructions.
5. **No Arbitrary Shell Execution:**
   - The memory and heartbeat adapter exposes structured Python/CLI functions only and never passes user/agent text to a shell.
