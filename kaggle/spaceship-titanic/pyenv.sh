#!/bin/bash

# Ask the user if they want to remove the existing .venv
read -p "Do you want to remove the existing .venv? (y/n): " choice

# Check the user's response
if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
    # Remove the existing .venv if the user agrees
    echo "Removing existing .venv..."
    rm -rf .venv
fi

# Create a new virtual environment
echo "Creating new .venv..."
python3.11 -m venv .venv
sleep 5

# Make the activate script executable
chmod +x .venv/bin/activate

# Activate the virtual environment
echo "Activating .venv..."
source .venv/bin/activate

echo "Virtual environment set up and activated."

# pip install -r requirements.txt
# python -m ipykernel install --user --name=myenv_3.11 --display-name "Python (myenv_3.11)"
