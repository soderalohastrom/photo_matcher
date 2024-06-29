#!/usr/bin/env bash
set -o errexit

python --version
pip install --upgrade pip
pip install -r requirements.txt

echo "Build script completed"