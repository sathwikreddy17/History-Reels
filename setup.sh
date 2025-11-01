#!/bin/bash

# Myth Factory Setup Script
# Phase 1+2 - Production Ready Setup

echo "🏛️ Myth Factory - Automated Mythology Video Generator"
echo "Setting up Phase 1+2 - Production Ready System..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if FFmpeg is installed
echo ""
echo "📋 Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Installing with Homebrew..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ Homebrew not found. Please install FFmpeg manually:"
        echo "   brew install ffmpeg"
        exit 1
    fi
else
    echo "✅ FFmpeg is installed"
    ffmpeg -version | head -1
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Check .env configuration
echo ""
echo "🔑 Checking API key configuration..."
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  Please update your OpenAI API key in .env file"
fi

if grep -q "your_elevenlabs_api_key_here" .env; then
    echo "⚠️  Please update your ElevenLabs API key in .env file"
fi

echo ""
echo "🎨 Asset Status Check:"
echo "Background images: $(ls assets/backgrounds/*.{jpg,png} 2>/dev/null | wc -l | tr -d ' ') found"
echo "Music tracks: $(ls assets/music/*.mp3 2>/dev/null | wc -l | tr -d ' ') found"
echo "Intro clips: $(ls assets/intros/*.mp4 2>/dev/null | wc -l | tr -d ' ') found"
echo "Outro clips: $(ls assets/outros/*.mp4 2>/dev/null | wc -l | tr -d ' ') found"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Update your API keys in .env file"
echo "2. Add background images to assets/backgrounds/"
echo "3. Add a music track to assets/music/"
echo "4. (Optional) Add intro.mp4 and outro.mp4"
echo "5. Run your first video: python3 main.py"
echo ""
echo "📚 Check README.md for detailed instructions"
echo "🎬 Your enhanced system includes Phase 1+2 features:"
echo "   • Ken Burns effects on backgrounds"
echo "   • Professional audio mixing"
echo "   • Auto thumbnails and monthly organization"
