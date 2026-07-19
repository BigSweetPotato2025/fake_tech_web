#!/bin/bash
set -e

CONFIG_FILE="config/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

REMOTE_HOST=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['deploy']['remote_host'])")
REMOTE_PATH=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['deploy']['remote_path'])")

echo "=== Deploying Developer Atlas ==="
echo "Target: $REMOTE_HOST:$REMOTE_PATH"

echo "[1/3] Building site..."
python3 builder/build.py

echo "[2/3] Deploying via rsync..."
rsync -avz --delete dist/ "$REMOTE_HOST:$REMOTE_PATH"

echo "[3/3] Deployment complete!"
