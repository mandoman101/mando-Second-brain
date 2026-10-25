#!/bin/zsh
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
while true; do
  /opt/homebrew/bin/python3 /Users/millie-girl/development/forgepoints-ai-lab/adapter/forgepoints_adapter.py sync-heartbeats >/dev/null 2>&1 || true
  sleep 10
done
