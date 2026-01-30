#!/bin/bash
echo "🚀 Initializing STP Kernel v2.0 Environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "❌ Error: requirements.txt not found."
    exit 1
fi

# Verification of package structure
if [ -f "stp/governor.py" ] && [ -f "stp/auditor.py" ]; then
    echo "✅ Core modules verified in stp/ directory."
else
    echo "❌ Error: Core modules missing in stp/ folder."
    exit 1
fi

echo "✨ Environment Ready. Run 'pytest' or 'python3 main.py' to start."
