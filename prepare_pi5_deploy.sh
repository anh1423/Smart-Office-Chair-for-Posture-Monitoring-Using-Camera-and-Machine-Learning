#!/bin/bash
# Deployment Package Creator for Raspberry Pi 5
# This script creates a clean deployment package excluding unnecessary files

set -e  # Exit on error

echo "=========================================="
echo "  Posture Monitor - Pi5 Deployment Prep  "
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/anh/DATN/webserver"
OUTPUT_DIR="/home/anh/DATN"
PACKAGE_NAME="posture-monitor-pi5.tar.gz"

echo -e "${YELLOW}Step 1: Cleaning up project...${NC}"
cd "$PROJECT_DIR"

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  ✓ Removed Python cache"

# Remove backup files
find . -type f -name "*.backup" -delete 2>/dev/null || true
find . -type f -name "*.bak" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true
echo "  ✓ Removed backup files"

# Remove logs
find . -type f -name "*.log" -delete 2>/dev/null || true
echo "  ✓ Removed log files"

# Remove node_modules if exists
rm -rf node_modules 2>/dev/null || true
echo "  ✓ Cleaned node_modules"

echo ""
echo -e "${YELLOW}Step 2: Verifying essential files...${NC}"

# Check for essential files
ESSENTIAL_FILES=(
    "app.py"
    "requirements-pi5.txt"
    "install-pi5.sh"
    "PI5_DEPLOYMENT_GUIDE.md"
    "config.py"
    "database/__init__.py"
    "database/models.py"
    "database/db_manager.py"
    "routes/"
    "templates/"
    "static/css/style.css"
    "static/js/"
    "models/"
    "utils/"
    "trained_models/"
)

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ Missing: $file"
        exit 1
    fi
done

echo ""
echo -e "${YELLOW}Step 3: Creating deployment package...${NC}"

cd "$OUTPUT_DIR"

# Create tarball excluding venv and other unnecessary files
tar -czf "$PACKAGE_NAME" \
    --exclude='webserver/venv' \
    --exclude='webserver/__pycache__' \
    --exclude='webserver/.git' \
    --exclude='webserver/*.log' \
    --exclude='webserver/*.pyc' \
    --exclude='webserver/node_modules' \
    --exclude='webserver/.vscode' \
    --exclude='webserver/.idea' \
    --exclude='webserver/tmp' \
    --exclude='webserver/temp' \
    --exclude='webserver/*.backup' \
    --exclude='webserver/*.bak' \
    webserver/

# Get package size
PACKAGE_SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)

echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ Deployment Package Created!"
echo "==========================================${NC}"
echo ""
echo "Package: $OUTPUT_DIR/$PACKAGE_NAME"
echo "Size: $PACKAGE_SIZE"
echo ""
echo "Next steps:"
echo "1. Transfer to Pi5:"
echo "   scp $PACKAGE_NAME pi@<PI_IP>:~/"
echo ""
echo "2. On Pi5, extract:"
echo "   tar -xzf $PACKAGE_NAME"
echo "   cd webserver"
echo ""
echo "3. Follow deployment guide:"
echo "   See pi5_deployment_guide.md"
echo ""
echo -e "${GREEN}Ready for deployment! 🚀${NC}"
