#!/bin/bash

echo "Setting up GTD application environment..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install pip if it's missing
echo "Ensuring pip is installed..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
rm get-pip.py

# Install flet with all dependencies
echo "Installing flet package..."
pip install 'flet[all]==0.27.5' --upgrade

# Install other requirements
echo "Installing other requirements..."
pip install -r requirements.txt

echo "Setup complete! You can now run the application."
