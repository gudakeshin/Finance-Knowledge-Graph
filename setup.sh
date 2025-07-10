#!/bin/bash

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR (required for pytesseract)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew install tesseract
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr
fi

# Create necessary directories
mkdir -p logs
mkdir -p data/uploads
mkdir -p data/processed

# Set up environment variables
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOL
fi

echo "Setup completed successfully!"
echo "Please update the .env file with your specific configuration values."
echo "To start the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the API server: uvicorn backend.main:app --reload"
echo "3. Start Celery worker: celery -A backend.app.services.celery_service worker --loglevel=info" 