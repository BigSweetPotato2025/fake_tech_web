#!/bin/bash
set -e

cd "$(dirname "$0")/.."
PROJECT_DIR=$(pwd)

export PYTHONPATH="$PROJECT_DIR"
export PATH="$PATH:$PROJECT_DIR/node_modules/.bin"

CONFIG_FILE="$PROJECT_DIR/config/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

REMOTE_HOST=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['deploy']['remote_host'])" 2>/dev/null || true)
REMOTE_PATH=$(python3 -c "import yaml; print(yaml.safe_load(open('$CONFIG_FILE'))['deploy']['remote_path'])" 2>/dev/null || true)

echo "=== Deploying Developer Atlas ==="
echo "Target: ${REMOTE_HOST:-local}:${REMOTE_PATH:-dist/}"

# Build to temp dir for atomic deploy
TMPDIR=$(mktemp -d /tmp/devatlas_build.XXXXXX)
trap "rm -rf $TMPDIR" EXIT

echo "[1/3] Building site..."
python3 builder/build.py --config "$CONFIG_FILE" --output "$TMPDIR/dist" -v || {
    echo "Full build failed, retrying with cache..."
    python3 builder/build.py --config "$CONFIG_FILE" --output "$TMPDIR/dist" --skip-fetch -v
}

# Compile TailwindCSS
echo "[1.5/3] Compiling CSS..."
mkdir -p "$TMPDIR/dist/assets/css"
npx tailwindcss --minify \
    -i "$PROJECT_DIR/assets/css/input.css" \
    -o "$TMPDIR/dist/assets/css/output.css"

# Validate output
if [ ! -f "$TMPDIR/dist/index.html" ]; then
    echo "Error: build output invalid (missing index.html)"
    exit 1
fi

if [ -n "$REMOTE_HOST" ] && [ -n "$REMOTE_PATH" ]; then
    echo "[2/3] Deploying via rsync to $REMOTE_HOST:$REMOTE_PATH ..."
    rsync -avz --delete "$TMPDIR/dist/" "$REMOTE_HOST:$REMOTE_PATH"
else
    echo "[2/3] Deploying locally (atomic swap)..."
    rm -rf "$PROJECT_DIR/dist.bak"
    [ -d "$PROJECT_DIR/dist" ] && mv "$PROJECT_DIR/dist" "$PROJECT_DIR/dist.bak"
    mv "$TMPDIR/dist" "$PROJECT_DIR/dist"
    rm -rf "$PROJECT_DIR/dist.bak"
fi

echo "[3/3] Deployment complete!"
