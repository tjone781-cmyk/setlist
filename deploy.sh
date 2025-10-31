#!/bin/bash

# Deployment script for setlist project
# Synchronizes Python files and data to remote server

# Configuration
REMOTE_HOST="192.168.1.206"
REMOTE_USER="tjone"  # Change this to your username on the remote server
REMOTE_PATH="/home/$REMOTE_USER/setlist_app"  # Using existing setlist_app directory
LOCAL_PATH="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting deployment to $REMOTE_HOST...${NC}"

# Check if SSH connection is available
echo -e "${YELLOW}📡 Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $REMOTE_USER@$REMOTE_HOST 'exit' 2>/dev/null; then
    echo -e "${RED}❌ SSH connection failed. Please check:${NC}"
    echo "   - Server is running and accessible"
    echo "   - SSH keys are configured or you have password access"
    echo "   - Username and IP address are correct"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Create remote directory if it doesn't exist
echo -e "${YELLOW}📁 Creating remote directory structure...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_PATH"

# Sync files (excluding virtual environment and cache files)
echo -e "${YELLOW}📦 Synchronizing files...${NC}"
rsync -avz --progress \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.git/' \
    --exclude='.vscode/' \
    --exclude='*.log' \
    $LOCAL_PATH/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ File synchronization completed successfully!${NC}"
else
    echo -e "${RED}❌ File synchronization failed${NC}"
    exit 1
fi

# Set up Python virtual environment on remote server
echo -e "${YELLOW}🐍 Setting up Python environment on remote server...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
cd ~/setlist_app
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la

# Check if Python 3.12 is available, fallback to python3
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "Using Python 3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "Using Python 3 ($(python3 --version))"
else
    echo "❌ No Python 3 installation found"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -eq 0 ]; then
        echo "✅ Virtual environment created"
    else
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install requirements if they exist
source venv/bin/activate
echo "Virtual environment activated"

# Install/update pip
pip install --upgrade pip

# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found, skipping package installation"
fi

echo "✅ Remote setup completed"
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Remote Python environment setup completed!${NC}"
else
    echo -e "${RED}❌ Remote Python environment setup failed${NC}"
    exit 1
fi

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && ls -la && source venv/bin/activate && python --version"

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}📋 Summary:${NC}"
echo "   • Files synchronized to: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"
echo "   • Python virtual environment configured"
echo "   • Ready to run: ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_PATH && source venv/bin/activate && python main.py'"