#!/usr/bin/env bash
# exit on error
set -o errexit

# Print Python version
python --version

# Update package lists
sudo apt-get update

# Install build essentials and CMake
sudo apt-get install -y build-essential cmake

# Install OpenBLAS and LAPACK for optimizations
sudo apt-get install -y libopenblas-dev liblapack-dev 

# We don't need to install Python as it's already available in the Render environment
# But we'll make sure pip is up to date
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install dlib
DLIB_VERSION=19.24.0
pip install dlib==${DLIB_VERSION} --no-cache-dir

# Install face_recognition
pip install face_recognition