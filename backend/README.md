# Backend

This is the backend service for the Finance Knowledge Graph project.

## Setup

1. Create a virtual environment using Python 3.11:
   ```bash
   python3.11 -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install development dependencies (optional):
   ```bash
   pip install -r requirements-dev.txt
   ```

## Running the Server

Always start the server using the virtual environment interpreter to ensure the correct Python version is used:

```bash
source venv/bin/activate
python -m uvicorn backend.main:app --reload --reload-dir backend
```

Note: Using `--reload-dir backend` (or pinning `watchfiles==0.21.0`) prevents the reloader from scanning the entire repository, improving performance. 