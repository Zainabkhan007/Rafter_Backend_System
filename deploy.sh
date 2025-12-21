#!/bin/bash
# Deployment script for Rafter Backend on EC2

set -e  # Exit on error

echo "======================================"
echo "  Rafter Backend Deployment Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/rafter-backend"
VENV_DIR="$PROJECT_DIR/venv"
REPO_URL="https://github.com/YOUR-USERNAME/Rafter_Backend_System.git"

# Functions
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running as correct user
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root"
    exit 1
fi

# Navigate to project directory
cd $PROJECT_DIR || exit 1

# Step 1: Pull latest code
print_status "Pulling latest code from repository..."
git pull origin main || git pull origin master

# Step 2: Activate virtual environment
print_status "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Step 3: Install/update dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements-prod.txt

# Step 4: Run migrations
print_status "Running database migrations..."
python manage.py migrate --noinput

# Step 5: Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Step 6: Restart Gunicorn
print_status "Restarting Gunicorn..."
sudo systemctl restart gunicorn

# Step 7: Restart Nginx
print_status "Restarting Nginx..."
sudo systemctl restart nginx

# Step 8: Check service status
echo ""
echo "Checking service status..."
if systemctl is-active --quiet gunicorn; then
    print_status "Gunicorn is running"
else
    print_error "Gunicorn is not running!"
    sudo systemctl status gunicorn
    exit 1
fi

if systemctl is-active --quiet nginx; then
    print_status "Nginx is running"
else
    print_error "Nginx is not running!"
    sudo systemctl status nginx
    exit 1
fi

echo ""
echo "======================================"
echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
echo "======================================"
echo ""
echo "View logs:"
echo "  Gunicorn: sudo journalctl -u gunicorn -f"
echo "  Nginx: sudo tail -f /var/log/nginx/error.log"
echo ""
