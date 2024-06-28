#!/usr/bin/env bash
# exit on error
set -o errexit

# Install build essentials and CMake
apt-get update && apt-get install -y cmake build-essential

# Install Python dependencies
pip install -r requirements.txt

# Additional commands to build dlib if necessary
pip install dlib --no-cache-dir
pip install face_recognition