#!/usr/bin/env bash
# exit on error
set -o errexit

# Print Python version
python --version

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install dlib
DLIB_VERSION=19.24.0
pip install dlib==${DLIB_VERSION} --no-cache-dir

# Install face_recognition
pip install face_recognition