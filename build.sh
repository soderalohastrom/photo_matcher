#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Additional commands to build dlib if necessary
pip install cmake
pip install dlib --no-cache-dir
pip install face_recognition