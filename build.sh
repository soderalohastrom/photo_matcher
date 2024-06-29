#!/usr/bin/env bash
# exit on error
set -o errexit

# Print Python version
python --version

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Try to install dlib using different methods
install_dlib() {
    # Method 1: Try to install the specified version
    pip install dlib==19.24.0 --no-cache-dir && return 0

    # Method 2: Try to install the latest version
    pip install dlib --no-cache-dir && return 0

    # Method 3: Try to install a pre-built wheel
    pip install https://github.com/jloh02/dlib/releases/download/v19.22/dlib-19.22.99-cp311-cp311-linux_x86_64.whl && return 0

    # Method 4: Build from source
    git clone https://github.com/davisking/dlib.git
    cd dlib
    mkdir build
    cd build
    cmake ..
    cmake --build .
    cd ..
    python setup.py install
    cd ..
    rm -rf dlib
}

# Attempt to install dlib
install_dlib || echo "Failed to install dlib"

# Install face_recognition
pip install face_recognition

echo "Build script completed"