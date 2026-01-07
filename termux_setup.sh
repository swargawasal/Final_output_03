#!/bin/bash

echo "🤖 Termux Auto-Setup for Transformative Bot (Venv Edition)"
echo "=========================================================="

echo "📦 Updating repositories..."
pkg update -y && pkg upgrade -y

echo "📦 Installing System Dependencies & Python..."
# Core build tools, python, git, and media libraries
# Note: User strictly requires Python 3.10 for compatibility.
pkg install -y tur-repo 
pkg install -y python3.10 git clang make binutils
# Build tools for compiling python packages (Numpy, Pillow, OpenCV fallback)
pkg install -y cmake ninja rust libffi libjpeg-turbo libpng freetype libxml2 libxslt zlib video-processing

echo "🛠️ Creating Virtual Environment (venv)..."
if ! command -v python3.10 &> /dev/null; then
    echo "❌ ERROR: Python 3.10 could not be installed. Termux 'tur-repo' might be missing or unreachable."
    echo "   Numpy/OpenCV require Python 3.10. Aborting."
    exit 1
fi

if [ ! -d "venv" ]; then
    python3.10 -m venv venv
    echo "   └─ Created 'venv' using Python 3.10"
else
    echo "   └─ 'venv' already exists. Skipping creation."
fi

echo "🔌 Activating venv..."
source venv/bin/activate

echo "📦 Upgrading pip (inside venv)..."
pip install --upgrade pip

echo "📦 Installing Python Dependencies (inside venv)..."
# Flag to force compile if wheels missing
export CFLAGS="-Wno-error=incompatible-function-pointer-types"
pip install -r requirements.txt

echo "=========================================================="
echo "✅ Setup Complete!"
echo ""
echo "❗ IMPORTANT ❗"
echo "To run the bot, you must activate the environment first:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "Or run in one line:"
echo "   ./venv/bin/python main.py"
