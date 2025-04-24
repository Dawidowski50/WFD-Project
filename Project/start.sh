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

# Check if manage.py exists
if ! file_exists "manage.py"; then
    echo "Error: manage.py not found. Please run this script from the project root directory."
    exit 1
fi

# Clear the terminal
clear

echo "Starting Equipment Rental System..."
echo "Once the server starts, you can access:"
echo "- Website: http://127.0.0.1:8000"
echo "- Admin Panel: http://127.0.0.1:8000/admin"
echo ""
echo "Default users:"
echo "- Admin: admin@admin.com (password: password)"
echo "- Manager: manager@manager.com (password: password)"
echo "- Staff: staff@staff.com (password: password)"
echo "- Customer: user1@user1.com (password: password)"
echo ""
echo "To stop the server, press CTRL+C"
echo "-----------------------------------"
echo ""

# Start the Django server
python3 manage.py runserver 