#!/bin/bash
# Installation script for Raspberry Pi 5
# Handles Python 3.12 compatibility

set -e

echo "=========================================="
echo "  Pi5 Installation Script"
echo "=========================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Detected Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.12" ]]; then
    echo "✓ Using Pi5-specific requirements (Python 3.12)"
    REQUIREMENTS_FILE="requirements-pi5.txt"
else
    echo "✓ Using standard requirements"
    REQUIREMENTS_FILE="requirements.txt"
fi

echo ""
echo "Step 1: Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"

echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Step 3: Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Step 4: Installing system dependencies first..."
# Install numpy and opencv separately for better compatibility
pip install numpy>=1.26.0
pip install opencv-python==4.10.0.84

echo ""
echo "Step 5: Installing PyTorch (this may take 10-20 minutes)..."
# Install PyTorch with CPU-only version for Pi5
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo ""
echo "Step 6: Installing remaining dependencies..."
# Install other packages
pip install Flask==3.0.0
pip install Flask-Login==0.6.3
pip install Flask-CORS==4.0.0
pip install Werkzeug==3.0.1
pip install SQLAlchemy>=2.0.35
pip install PyMySQL==1.1.0
pip install cryptography==41.0.7
pip install bcrypt==4.1.2
pip install psutil==5.9.6
pip install Pillow>=11.0.0
pip install paho-mqtt==1.6.1
pip install python-dotenv==1.0.0

echo ""
echo "Step 7: Installing Ultralytics..."
pip install ultralytics>=8.3.0

echo ""
echo "Step 8: Installing ML dependencies..."
pip install joblib scikit-learn scipy

echo ""
echo "=========================================="
echo "  ✓ Installation Complete!"
echo "=========================================="
echo ""
echo "Installed packages:"
pip list | grep -E "(torch|ultralytics|opencv|Flask)"
echo ""
echo "Next steps:"
echo "1. Configure database in .env file"
echo "2. Run: python3 app.py"
echo ""
