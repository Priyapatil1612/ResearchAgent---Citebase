#!/bin/bash
set -e

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies with specific build options
PIP_ONLY_BINARY=:all: \
PIP_FIND_LINKS="https://download.pytorch.org/whl/torch_stable.html" \
pip install --no-cache-dir \
    --only-binary=:all: \
    -r requirements.txt