#!/bin/bash
# Start Caddy for local development
# Usage: bash scripts/start_local.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting Caddy on http://localhost:8080 ..."
echo "Project: $PROJECT_DIR/dist"
echo "Press Ctrl+C to stop."
echo ""

caddy run --config "$PROJECT_DIR/Caddyfile"
