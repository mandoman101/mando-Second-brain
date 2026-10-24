# Testing & Verification Guide

## 1. Upstream Obsidian Second Brain Tests
```bash
/opt/homebrew/bin/uv run --directory upstream/obsidian-second-brain pytest tests/test_mcp_vault_ops_safety.py tests/test_mcp_bookkeeping.py tests/test_mcp_fresh_vault_health.py
```

## 2. Upstream Hypernovum Tests
```bash
cd upstream/hypernovum && npm test
```

## 3. ForgePoints Milestone 1 Integration Tests
```bash
/opt/homebrew/bin/uv run --directory upstream/obsidian-second-brain pytest ../../tests/test_forgepoints_milestone1.py -v
```
