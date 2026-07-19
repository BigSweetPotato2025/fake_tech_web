#!/bin/bash
set -e

echo "=== Developer Atlas Setup ==="

echo "[1/4] Checking Python..."
python3 --version

echo "[2/4] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[3/4] Installing Python dependencies..."
pip install -r requirements.txt

echo "[4/4] Setting up TailwindCSS..."
npm install

echo ""
echo "=== Setup Complete ==="
echo "Run 'source venv/bin/activate' to activate virtual environment"
echo "Run 'python builder/build.py' to build the site"
