#!/usr/bin/env bash
# Exit on any error
set -o errexit

echo "==> Step 1: Installing Python backend dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Step 2: Checking Node.js environment..."
if ! command -v npm &> /dev/null; then
    echo "Node.js/npm not found. Downloading standalone Node.js..."
    NODE_VERSION=v20.18.0
    curl -fsSL "https://nodejs.org/dist/${NODE_VERSION}/node-${NODE_VERSION}-linux-x64.tar.gz" | tar -xz -C /tmp/
    export PATH="/tmp/node-${NODE_VERSION}-linux-x64/bin:$PATH"
fi

echo "==> Step 3: Building React frontend bundle..."
cd frontend
npm install
npm run build
cd ..

echo "==> Build complete! Ready to start AI LifePilot."
