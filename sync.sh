#!/bin/bash

# Quick sync script - just synchronizes files without environment setup
# Usage: ./sync.sh

REMOTE_HOST="192.168.1.206"
REMOTE_USER="tjone"
REMOTE_PATH="/home/$REMOTE_USER/setlist_app"

echo "🔄 Quick sync to $REMOTE_HOST..."

rsync -avz --progress \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.git/' \
    --exclude='.vscode/' \
    --exclude='*.log' \
    . $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

if [ $? -eq 0 ]; then
    echo "✅ Sync completed!"
    echo "📋 Run on server: ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_PATH && python main.py'"
else
    echo "❌ Sync failed!"
fi