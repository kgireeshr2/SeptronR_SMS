#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  SMS Backend — Server Setup Script (Ubuntu 22.04)
#  Run once on a fresh server: sudo bash setup.sh
# ═══════════════════════════════════════════════════════════
set -e

echo "→ Installing system packages..."
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3-pip mysql-server redis-server nginx git curl

echo "→ Starting MySQL..."
systemctl enable mysql && systemctl start mysql

echo "→ Creating MySQL database and user..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS sms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
mysql -u root -e "CREATE USER IF NOT EXISTS 'sms_user'@'localhost' IDENTIFIED BY 'sms_pass';" 2>/dev/null || true
mysql -u root -e "GRANT ALL PRIVILEGES ON sms_db.* TO 'sms_user'@'localhost'; FLUSH PRIVILEGES;" || true

echo "→ Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "→ Setting up uploads directory..."
mkdir -p uploads

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete!"
echo "  Next steps:"
echo "  1. cp .env.example .env"
echo "  2. Edit .env with your settings"
echo "  3. bash run.sh"
echo "  4. POST /api/v1/install with your INSTALL_SECRET_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
