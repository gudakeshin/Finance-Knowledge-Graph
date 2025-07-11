# Stop Script - Quick Reference

## 🚀 Quick Start

```bash
# Stop everything
./stop.sh

# Check status
./stop.sh --status

# Force kill if stuck
./stop.sh --force
```

## 📋 Common Commands

| Command | What it does |
|---------|-------------|
| `./stop.sh` | Stop all services gracefully |
| `./stop.sh --status` | Show what's running |
| `./stop.sh --force` | Force kill everything |
| `./stop.sh --dry-run` | See what would be stopped |
| `./stop.sh --backend` | Stop only backend |
| `./stop.sh --frontend` | Stop only frontend |
| `./stop.sh --celery` | Stop only Celery |
| `./stop.sh --infra` | Stop only Redis/Neo4j |

## 🔧 Troubleshooting

```bash
# If graceful stop fails
./stop.sh --force

# Check if ports are free
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Manual cleanup (if script fails)
pkill -f uvicorn
pkill -f vite
pkill -f celery
```

## 📊 Status Indicators

- 🟢 **Running** - Service is active
- 🔴 **Stopped** - Service is not running
- ⚠️ **Warning** - Graceful stop failed, force killing
- ✅ **Success** - Process stopped successfully

## 🎯 Use Cases

### Normal Shutdown
```bash
./stop.sh
```

### Restart Backend Only
```bash
./stop.sh --backend
python3 start_app.py
```

### Check Before Stopping
```bash
./stop.sh --status
./stop.sh --dry-run
./stop.sh
```

### Emergency Stop
```bash
./stop.sh --force
```

## 📝 Notes

- **Safe**: Only stops processes, doesn't delete data
- **Graceful**: Tries SIGTERM first, then SIGKILL
- **Smart**: Finds processes by port and command patterns
- **Complete**: Stops backend, frontend, Celery, Redis, Neo4j

---

**Full Documentation**: See `STOP_SCRIPT_DOCUMENTATION.md` for detailed information. 