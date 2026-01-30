#!/bin/bash
# STP v2.0-RFC Environment Setup

echo "🚀 Initializing STP Kernel v2.0 Environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify repository solvency
if [ -f "governor.py" ] && [ -f "auditor.py" ]; then
    echo "✅ Kernel modules (governor.py, auditor.py) detected."
else
    echo "❌ Error: Core modules missing. Ensure governor.py and auditor.py are in the root."
    exit 1
fi

echo "✨ Setup complete. Run 'source venv/bin/activate' to begin."
