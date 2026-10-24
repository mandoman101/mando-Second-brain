# Configuration Guide

All hostnames, endpoints, paths, and project mappings are externalized in `adapter/config.example.json` (or overridden via environment variables). Nothing is hardcoded in application logic.

## Environment Variables
- `FORGEPOINTS_CONFIG`: Path to JSON config file (defaults to `adapter/config.example.json`).
- `OBSIDIAN_VAULT_PATH`: Override target Obsidian vault path (defaults to `/Users/millie-girl/development/forgepoints-ai-lab/test-vault`).
- `FORGEPOINTS_TELEMETRY_URL`: Local telemetry endpoint (defaults to `http://127.0.0.1:18795/api/metrics`).
