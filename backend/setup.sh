#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting Finance Knowledge Graph setup..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install core dependencies first
echo "📥 Installing core dependencies..."
pip install fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.11.5 \
    pydantic-settings==2.9.1 \
    python-dotenv==1.0.0 \
    neo4j==5.14.1 \
    celery==5.3.6 \
    redis==5.0.1 \
    spacy==3.8.7

# Download spaCy model
echo "📚 Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Kill any existing processes on port 8000
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start the FastAPI server
echo "🌐 Starting FastAPI server..."
python -m uvicorn backend.main:app --reload --port 8000 