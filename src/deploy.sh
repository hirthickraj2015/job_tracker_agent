#!/bin/bash

# Job Tracker Agent Deployment Script
echo "🚀 Setting up Job Tracker Agent..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "📁 Project directory: $PROJECT_DIR"

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Created virtual environment"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "✅ Activated virtual environment"

# Upgrade pip
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Installed Python dependencies"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Make scripts executable
chmod +x scripts/*.sh
echo "✅ Made scripts executable"

# Create systemd service file (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SERVICE_FILE="/etc/systemd/system/job-tracker.service"
    
    if [ ! -f "$SERVICE_FILE" ]; then
        sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Job Tracker Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/src/job_tracker.py --schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        echo "✅ Created systemd service file"
        echo "📝 To start the service: sudo systemctl start job-tracker"
        echo "📝 To enable on boot: sudo systemctl enable job-tracker"
    else
        echo "✅ Systemd service already exists"
    fi
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit config/job_config.json with your preferences"
echo "2. Add your email credentials to the config file"
echo "3. Test with: ./scripts/run.sh --run-once"
echo "4. For continuous operation: ./scripts/run.sh --schedule"
echo ""
echo "📁 Project structure:"
echo "   - Configuration: config/job_config.json"
echo "   - Data: data/"
echo "   - Logs: logs/"
echo "   - Backups: backups/"
echo ""
echo "🔧 For support, check the README.md file."