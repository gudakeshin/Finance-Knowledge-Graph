# Finance Knowledge Graph - Stop Script Documentation

## Overview

The Finance Knowledge Graph application includes a comprehensive stop script that gracefully terminates all running services. This script is designed to safely shut down the entire application stack, including backend, frontend, Celery workers, and infrastructure services.

## Files

- **`stop_app.py`** - Main Python stop script
- **`stop.sh`** - Shell script wrapper for easier usage

## Features

### 🔍 Intelligent Process Detection
- Finds processes by port numbers (8000, 5173, 6379, 7474)
- Identifies processes by command patterns (uvicorn, vite, celery, redis, neo4j)
- Combines multiple detection methods for comprehensive coverage

### 🛡️ Graceful Shutdown
- Attempts graceful termination first (SIGTERM)
- Waits up to 10 seconds for graceful shutdown
- Falls back to force kill (SIGKILL) if needed
- Prevents data corruption and ensures clean shutdown

### 📊 Status Monitoring
- Real-time status checking of all services
- Port availability verification
- Process count reporting
- Clear visual indicators (🟢 Running, 🔴 Stopped)

### 🎯 Selective Stopping
- Stop all services at once
- Stop specific services individually
- Infrastructure-only stopping
- Dry-run mode for testing

## Installation

### Prerequisites

1. **Python 3.6+** (already installed)
2. **psutil library** (automatically installed by the script)

```bash
# Install psutil if not already installed
python3 -m pip install psutil
```

### Setup

```bash
# Make the shell script executable
chmod +x stop.sh
```

## Usage

### Method 1: Shell Script (Recommended)

```bash
# Stop all services
./stop.sh

# Stop specific services
./stop.sh --backend
./stop.sh --frontend
./stop.sh --celery
./stop.sh --infra

# Force kill (not graceful)
./stop.sh --force

# Check status without stopping
./stop.sh --status

# Dry run (see what would be stopped)
./stop.sh --dry-run
```

### Method 2: Python Directly

```bash
# Stop all services
python3 stop_app.py

# Stop specific services
python3 stop_app.py --backend
python3 stop_app.py --frontend
python3 stop_app.py --celery
python3 stop_app.py --infra

# Force kill
python3 stop_app.py --force

# Check status
python3 stop_app.py --status

# Dry run
python3 stop_app.py --dry-run
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--all` | Stop all services (default) | `./stop.sh --all` |
| `--backend` | Stop only backend server | `./stop.sh --backend` |
| `--frontend` | Stop only frontend server | `./stop.sh --frontend` |
| `--celery` | Stop only Celery worker | `./stop.sh --celery` |
| `--infra` | Stop only infrastructure (Redis, Neo4j) | `./stop.sh --infra` |
| `--force` | Force kill processes (not graceful) | `./stop.sh --force` |
| `--dry-run` | Show what would be stopped without actually stopping | `./stop.sh --dry-run` |
| `--status` | Show current status of all services | `./stop.sh --status` |

## Service Detection

The script detects services using multiple methods:

### Port-Based Detection
- **Backend**: Port 8000 (FastAPI/Uvicorn)
- **Frontend**: Port 5173 (Vite dev server)
- **Redis**: Port 6379 (Redis server)
- **Neo4j**: Port 7474 (Neo4j database)

### Process Pattern Detection
- **Backend**: `uvicorn`, `python.*main.py`, `python.*start_app.py`
- **Frontend**: `vite`, `npm.*dev`, `node.*vite`
- **Celery**: `celery.*worker`, `python.*celery`
- **Redis**: `redis-server`, `redis.*6379`
- **Neo4j**: `neo4j`, `java.*neo4j`

## Examples

### Basic Usage

```bash
# Quick stop everything
./stop.sh

# Check what's running first
./stop.sh --status

# Stop only the backend (if you want to restart it)
./stop.sh --backend

# Force kill everything (use if graceful stop fails)
./stop.sh --force
```

### Advanced Usage

```bash
# Stop only infrastructure services
./stop.sh --infra

# Stop frontend and backend but leave Celery running
./stop.sh --frontend --backend

# See what would be stopped without doing it
./stop.sh --dry-run

# Check status after stopping
./stop.sh && ./stop.sh --status
```

### Troubleshooting

```bash
# If graceful stop fails, use force
./stop.sh --force

# Check if processes are still running
./stop.sh --status

# Stop specific service that's stuck
./stop.sh --backend --force
```

## Output Examples

### Status Check
```
📊 Current service status:
  Backend: 🟢 Running
  Frontend: 🟢 Running
  Redis: 🔴 Stopped
  Neo4j: 🔴 Stopped
  Backend processes: 2 found
  Frontend processes: 1 found
  Celery processes: None found
```

### Stopping Services
```
🛑 Stopping all Finance Knowledge Graph services...
🛑 Stopping frontend server...
Found 1 frontend process(es)
Gracefully stopping process 12345 (node)
✅ Process 12345 stopped gracefully
🛑 Stopping backend server...
Found 2 backend process(es)
Gracefully stopping process 67890 (uvicorn)
✅ Process 67890 stopped gracefully
✅ All requested services stopped successfully
```

### Dry Run
```
🔍 DRY RUN - Would stop the following:
📊 Current service status:
  Backend: 🟢 Running
  Frontend: 🟢 Running
  Redis: 🔴 Stopped
  Neo4j: 🔴 Stopped
```

## Error Handling

### Common Issues

1. **Permission Denied**
   ```bash
   # Solution: Use sudo if needed
   sudo ./stop.sh
   ```

2. **Process Not Found**
   ```
   ℹ️  No backend processes found
   ```
   This is normal if services are already stopped.

3. **Graceful Shutdown Fails**
   ```
   ⚠️  Process 12345 didn't stop gracefully, force killing
   ```
   The script automatically falls back to force kill.

### Troubleshooting Commands

```bash
# Check if ports are in use
lsof -i :8000  # Backend
lsof -i :5173  # Frontend
lsof -i :6379  # Redis
lsof -i :7474  # Neo4j

# Check running processes
ps aux | grep uvicorn
ps aux | grep vite
ps aux | grep celery
ps aux | grep redis
ps aux | grep neo4j

# Manual force kill (if script fails)
pkill -f uvicorn
pkill -f vite
pkill -f celery
pkill -f redis-server
pkill -f neo4j
```

## Integration with Start Script

The stop script works seamlessly with the start script (`start_app.py`):

```bash
# Start the application
python3 start_app.py

# Stop the application
./stop.sh

# Restart the application
./stop.sh && python3 start_app.py
```

## Safety Features

### Graceful Shutdown Process
1. **SIGTERM Signal**: Sends termination signal to processes
2. **10-Second Wait**: Allows time for graceful shutdown
3. **SIGKILL Fallback**: Force kills if graceful shutdown fails
4. **Status Verification**: Confirms processes are actually stopped

### Data Protection
- **No Data Loss**: Graceful shutdown prevents corruption
- **Connection Cleanup**: Properly closes database connections
- **File System Safety**: Doesn't delete any data files
- **PID Tracking**: Cleans up process tracking files

## Configuration

### Customizing Ports
Edit `stop_app.py` to change default ports:

```python
self.backend_port = 8000    # Change if needed
self.frontend_port = 5173   # Change if needed
self.celery_port = 6379     # Redis port
self.neo4j_port = 7474      # Neo4j port
```

### Adding New Services
To detect additional services, add patterns to `service_patterns`:

```python
self.service_patterns = {
    'new_service': [
        'new-service-pattern',
        'another-pattern'
    ],
    # ... existing patterns
}
```

## Best Practices

### When to Use Different Options

1. **Normal Shutdown**: `./stop.sh` (graceful)
2. **Stuck Processes**: `./stop.sh --force`
3. **Partial Restart**: `./stop.sh --backend && python3 start_app.py`
4. **Infrastructure Only**: `./stop.sh --infra`
5. **Testing**: `./stop.sh --dry-run`

### Recommended Workflow

```bash
# 1. Check current status
./stop.sh --status

# 2. Stop all services
./stop.sh

# 3. Verify everything is stopped
./stop.sh --status

# 4. Restart if needed
python3 start_app.py
```

## Troubleshooting Guide

### Script Won't Run
```bash
# Check Python installation
python3 --version

# Check psutil installation
python3 -c "import psutil; print('psutil installed')"

# Install psutil if missing
python3 -m pip install psutil
```

### Services Won't Stop
```bash
# Use force kill
./stop.sh --force

# Check for zombie processes
ps aux | grep defunct

# Manual cleanup
pkill -9 -f uvicorn
pkill -9 -f vite
```

### Permission Issues
```bash
# Make script executable
chmod +x stop.sh

# Run with sudo if needed
sudo ./stop.sh
```

## Support

If you encounter issues:

1. **Check the status first**: `./stop.sh --status`
2. **Try force kill**: `./stop.sh --force`
3. **Check system processes**: `ps aux | grep <service>`
4. **Review logs**: Check application logs for errors
5. **Restart system**: As a last resort, restart your system

## Version History

- **v1.0**: Initial release with basic stop functionality
- **v1.1**: Added graceful shutdown and force kill options
- **v1.2**: Added status checking and dry-run mode
- **v1.3**: Improved process detection and error handling

---

**Note**: This script is designed to be safe and non-destructive. It only stops running processes and doesn't delete any data or configuration files. 