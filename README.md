# Setlist Project

A Python application for managing setlists with remote deployment capabilities.

## Features

- 🎵 Setlist management with JSON data storage
- 🚀 Automated deployment to remote servers via SSH
- 🔄 Quick file synchronization scripts
- 🐍 Python 3.12 virtual environment support

## Files

- `main.py` - Main Python application
- `setlist.json` - Setlist data storage
- `deploy.sh` - Full deployment script with environment setup
- `sync.sh` - Quick file synchronization script
- `requirements.txt` - Python dependencies

## Usage

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python main.py
```

### Deployment
```bash
# Full deployment (includes environment setup)
./deploy.sh

# Quick sync (files only)
./sync.sh
```

## Remote Server

- **Target**: 192.168.1.206 (Raspberry Pi)
- **Directory**: `/home/tjone/setlist_app`
- **Python**: 3.13.5

## Requirements

- Python 3.12+
- SSH access to remote server
- rsync for file synchronization

---

*Project initialized on October 30, 2025*