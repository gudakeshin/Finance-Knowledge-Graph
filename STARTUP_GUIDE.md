# Finance Knowledge Graph - Startup Guide

This guide explains how to start the Finance Knowledge Graph application using the new unified startup script.

## Quick Start

### Option 1: Using the Shell Script (Recommended)
```bash
# Start all services (including dependencies)
./start.sh

# Development mode (skip dependencies)
./start.sh --dev

# Custom ports
./start.sh --port-backend 9000 --port-frontend 3000
```

### Option 2: Using the Python Script Directly
```bash
# Start all services
python3 start_app.py

# Skip dependencies
python3 start_app.py --skip-deps

# Custom ports
python3 start_app.py --port-backend 9000 --port-frontend 3000
```

## What the Startup Script Does

The startup script automatically handles:

1. **Environment Setup**
   - Creates Python virtual environment if needed
   - Installs Python dependencies from `requirements.txt`
   - Installs frontend dependencies with `npm install`

2. **Dependency Services** (unless `--skip-deps` is used)
   - **Neo4j Database**: Starts Neo4j if not running
   - **Redis Server**: Starts Redis for Celery message broker

3. **Application Services**
   - **Backend API**: FastAPI server with uvicorn
   - **Celery Worker**: Background task processor
   - **Frontend**: React development server with Vite

4. **Monitoring & Health Checks**
   - Monitors all services for health
   - Automatically restarts failed services
   - Graceful shutdown on Ctrl+C

## Prerequisites

### Required Software
- **Python 3.8+**: For backend services
- **Node.js 16+**: For frontend development
- **npm**: Package manager for Node.js

### Optional Dependencies
- **Neo4j**: Graph database (will be started automatically if available)
- **Redis**: Message broker (will be started automatically if available)

## Installation Instructions

### Neo4j Installation

#### macOS
```bash
# Using Homebrew
brew install neo4j

# Or download from https://neo4j.com/download/
```

#### Ubuntu/Debian
```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
```

#### Using Docker
```bash
docker run -p 7474:7474 -p 7687:7687 neo4j:latest
```

### Redis Installation

#### macOS
```bash
brew install redis
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install redis-server
```

#### Using Docker
```bash
docker run -p 6379:6379 redis:latest
```

## Usage Examples

### Development Mode
```bash
# Skip dependencies (assumes Neo4j and Redis are running separately)
./start.sh --dev
```

### Production Mode
```bash
# Start everything including dependencies
./start.sh --prod
```

### Custom Configuration
```bash
# Use different ports
./start.sh --port-backend 9000 --port-frontend 3000

# Skip dependencies with custom ports
./start.sh --skip-deps --port-backend 9000 --port-frontend 3000
```

## Service URLs

Once started, the application will be available at:

- **Frontend**: http://localhost:5173 (or custom port)
- **Backend API**: http://localhost:8000 (or custom port)
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (if Neo4j is running)

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```
❌ Port 8000 is not available
```
**Solution**: Use a different port or stop the service using that port
```bash
./start.sh --port-backend 9000
```

#### 2. Neo4j Not Found
```
❌ Neo4j not found. Please install Neo4j first.
```
**Solution**: Install Neo4j or use `--skip-deps` flag
```bash
./start.sh --skip-deps
```

#### 3. Redis Not Found
```
❌ Redis not found. Please install Redis first.
```
**Solution**: Install Redis or use `--skip-deps` flag
```bash
./start.sh --skip-deps
```

#### 4. Python Dependencies Missing
```
❌ Failed to install dependencies
```
**Solution**: Check Python version and try manual installation
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 5. Frontend Dependencies Missing
```
❌ Failed to install frontend dependencies
```
**Solution**: Check Node.js version and try manual installation
```bash
cd frontend
npm install
```

### Manual Service Startup

If the automatic startup fails, you can start services manually:

#### Start Backend Only
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000

# In another terminal, start Celery worker
celery -A backend.app.services.celery_service worker --loglevel=info
```

#### Start Frontend Only
```bash
cd frontend
npm install
npm run dev
```

#### Start Dependencies Only
```bash
# Start Neo4j
neo4j start

# Start Redis
redis-server --daemonize yes
```

### Logs and Debugging

The startup script creates detailed logs:

- **Console Output**: Real-time status and error messages
- **Log File**: `startup.log` in the project root
- **Service Logs**: Check individual service logs for specific issues

### Health Checks

You can manually check if services are running:

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:5173

# Check Neo4j
curl http://localhost:7474

# Check Redis
redis-cli ping
```

## Advanced Configuration

### Environment Variables

Create a `.env` file in the project root for custom configuration:

```env
# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### Custom Celery Configuration

Modify `backend/app/services/celery_service.py` for custom Celery settings:

```python
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    # Add custom settings here
)
```

## Stopping the Application

### Graceful Shutdown
Press `Ctrl+C` in the terminal where the startup script is running. This will:
- Stop all services gracefully
- Clean up processes
- Save any pending work

### Force Shutdown
If graceful shutdown doesn't work:
```bash
# Find and kill processes
pkill -f "uvicorn"
pkill -f "celery"
pkill -f "vite"

# Or kill by port
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

## Performance Tuning

### For Development
```bash
# Use development mode (skip deps, faster startup)
./start.sh --dev
```

### For Production
```bash
# Start all services with production settings
./start.sh --prod

# Consider using production servers:
# - Gunicorn instead of uvicorn
# - PM2 for Node.js process management
# - Docker containers for isolation
```

## Support

If you encounter issues:

1. Check the logs in `startup.log`
2. Verify all prerequisites are installed
3. Try running services manually to isolate the issue
4. Check the individual service documentation in the project README

For additional help, refer to:
- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [API Documentation](http://localhost:8000/docs) (when running) 