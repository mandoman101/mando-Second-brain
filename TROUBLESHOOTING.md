# Troubleshooting

1. **`TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` when running `obsidian-second-brain` scripts:**
   - **Cause:** macOS `/usr/bin/python3` is Xcode Python `3.9.6`, which does not support `bool | None` at runtime.
   - **Fix:** Always invoke with `/opt/homebrew/bin/python3` (`3.14.3`) or `uv run`.
2. **Project note does not appear as a building in Hypernovum:**
   - Ensure frontmatter has `type: project` or `tags: [project]` and valid YAML.
3. **Agent orb does not attach to a building:**
   - Ensure `--cwd` in the heartbeat matches the project note's `projectDir`, or `--project` matches the note's `title`.
