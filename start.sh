#!/bin/bash
#
# Quick start script for development
# Tạo venv, cài dependencies, và chạy webserver
#

set -e

echo "=========================================="
echo "Webserver Quick Start"
echo "=========================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env with your configuration"
    echo ""
fi

# Test database connection
echo "🔍 Testing database connection..."
python3 test_db_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "🚀 Starting webserver..."
    echo "=========================================="
    echo ""
    echo "Dashboard will be available at:"
    echo "http://localhost:5000"
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Run webserver
    python3 app.py
else
    echo ""
    echo "❌ Database connection failed!"
    echo "Please check:"
    echo "1. MariaDB is running on Pi5"
    echo "2. .env file has correct DB_HOST"
    echo "3. See SETUP_REMOTE_DB.md for setup instructions"
    echo ""
    exit 1
fi
