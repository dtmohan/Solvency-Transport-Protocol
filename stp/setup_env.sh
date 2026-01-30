#!/bin/bash
# STP v2.0 Environment Setup Script

echo "Initializing STP v2.0 Kernel Environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify repository solvency
if [ -f "governor.py" ] && [ -f "auditor.py" ]; then
    echo "✅ Kernel modules detected."
else
    echo "❌ Error: Core modules (governor.py or auditor.py) missing."
    exit 1
fi

echo "Environment ready. Run 'source venv/bin/activate' to begin."
