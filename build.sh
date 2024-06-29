#!/usr/bin/env bash
set -o errexit

python --version
pip install --upgrade pip
pip install -r requirements.txt

# Print installed package versions for debugging
pip freeze

echo "Build script completed"