#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run deploy.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the job tracker
echo "🔍 Starting Job Tracker Agent..."
python src/job_tracker.py "$@"