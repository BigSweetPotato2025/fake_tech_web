#!/bin/bash
# Start Caddy for local development
# Usage: ./start.sh  (run from project root)

echo "Starting Caddy on http://localhost:8080 ..."
echo "Project: $(pwd)/dist"
echo "Press Ctrl+C to stop."
echo ""

caddy run --config "$(pwd)/Caddyfile"
