#!/usr/bin/env bash
set -o errexit

# Ensure we're using Python 3.10
pyenv install 3.10.9
pyenv global 3.10.9

python --version
pip install --upgrade pip
pip install -r requirements.txt

echo "Build script completed"