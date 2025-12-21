#!/bin/bash
# EC2 Initial Setup Script for Rafter Backend

set -e

echo "======================================"
echo "  EC2 Setup for Rafter Backend"
echo "======================================"
echo ""

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "Installing Python and dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev \
  postgresql-client libpq-dev nginx git \
  build-essential libssl-dev libffi-dev

# Create project directory
echo "Creating project directory..."
sudo mkdir -p /var/www/rafter-backend
sudo chown $USER:$USER /var/www/rafter-backend

# Clone repository (you'll need to provide the URL)
echo ""
echo "========================================="
echo "Next steps:"
echo "1. Clone your repository:"
echo "   cd /var/www/rafter-backend"
echo "   git clone YOUR-REPO-URL ."
echo ""
echo "2. Create virtual environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements-prod.txt"
echo ""
echo "3. Create .env file with your settings"
echo "4. Run: python manage.py migrate"
echo "5. Run: python manage.py collectstatic"
echo "6. Run: python manage.py createsuperuser"
echo "========================================="
echo ""
echo "✓ System setup complete!"
echo ""
