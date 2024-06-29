#!/usr/bin/env bash
set -o errexit

# Print Python version (should be set by Render.com)
python --version

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

echo "Build script completed"