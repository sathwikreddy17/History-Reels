#!/bin/bash
# Virtual Environment Activation Script
echo "🔧 Activating Myth Factory Virtual Environment..."
source myth-factory-env/bin/activate
echo "✅ Virtual environment activated!"
echo "📁 Current directory: $(pwd)"
echo "🐍 Python path: $(which python)"
echo ""
echo "🚀 Ready to run: python main.py"
echo "💡 Type 'deactivate' to exit the virtual environment when done"
exec "$SHELL"
