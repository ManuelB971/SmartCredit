#!/bin/bash

# Smart Crédit - Deployment Script
# Usage: ./deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
REPO_DIR="/var/www/smart-credit"
VENV_DIR="$REPO_DIR/venv"

echo "=== Smart Crédit Deployment ===="
echo "Environment: $ENVIRONMENT"
echo "Directory: $REPO_DIR"

# 1. Pull latest code
echo "→ Pulling latest code..."
cd $REPO_DIR
git pull origin main

# 2. Activate venv
echo "→ Activating virtual environment..."
source $VENV_DIR/bin/activate

# 3. Install dependencies
echo "→ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run migrations
echo "→ Running migrations..."
python manage.py migrate

# 5. Collect static files
echo "→ Collecting static files..."
python manage.py collectstatic --noinput

# 6. Clear cache
echo "→ Clearing cache..."
python manage.py clear_cache

# 7. Restart services
echo "→ Restarting services..."
sudo systemctl restart smart-credit
sudo systemctl restart nginx

# 8. Verify deployment
echo "→ Verifying deployment..."
sleep 2
curl -s http://localhost:8000/admin/ | grep -q "Django" && echo "✓ Server is running" || echo "✗ Server check failed"

echo ""
echo "=== Deployment Complete ===="
echo "App: https://smartcredit.fr"
