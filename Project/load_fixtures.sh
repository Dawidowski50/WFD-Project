#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a file exists
file_exists() {
    [ -f "$1" ]
}

# Check if Python is installed
if ! command_exists python3; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run 'python3 -m venv venv' first."
    exit 1
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "Error: Could not find virtual environment activation script"
    exit 1
fi

# Check if Django is installed
if ! python3 -c "import django" &>/dev/null; then
    echo "Error: Django is not installed. Please run 'pip install -r requirements.txt'"
    exit 1
fi

echo "Loading fixtures..."

# Array of fixture files to load
fixtures=(
    "users/fixtures/users.json"
    "core/fixtures/user_profiles.json"
    "inventory/fixtures/categories.json"
    "inventory/fixtures/items.json"
    "core/fixtures/maintenance.json"
)

# Load each fixture
for fixture in "${fixtures[@]}"; do
    if ! file_exists "$fixture"; then
        echo "Error: Fixture file not found: $fixture"
        exit 1
    fi
    
    echo "Loading $fixture..."
    if ! python3 manage.py loaddata "$fixture"; then
        echo "Error: Failed to load $fixture"
        exit 1
    fi
done

echo "Fixtures loaded successfully!" 