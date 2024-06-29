#!/usr/bin/env bash
set -o errexit

python --version
pip install --upgrade pip
pip install -r requirements.txt

install_dlib() {
    # Try pip install first
    pip install dlib==19.24.0 --no-cache-dir && return 0

    # If pip fails, build from source
    wget http://dlib.net/files/dlib-19.24.tar.bz2
    tar xvf dlib-19.24.tar.bz2
    cd dlib-19.24/
    mkdir build
    cd build
    cmake ..
    cmake --build . --config Release
    cd ..
    python setup.py install
    cd ..
    rm -rf dlib-19.24 dlib-19.24.tar.bz2
}

install_dlib || echo "Failed to install dlib"
pip install face_recognition

echo "Build script completed"