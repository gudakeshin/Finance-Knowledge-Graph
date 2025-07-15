#!/usr/bin/env python3
"""
Finance Knowledge Graph Application Startup Script

This script starts all components of the Finance Knowledge Graph application:
- Neo4j database (if not running)
- Redis server (if not running)
- Backend FastAPI server
- Celery worker for background tasks
- Frontend development server

Usage:
    python start_app.py [--port-backend 8000] [--port-frontend 5173] [--skip-deps]
"""

import os
import sys
import time
import signal
import subprocess
import threading
import argparse
import requests
import socket
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import json
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('startup.log')
    ]
)
logger = logging.getLogger(__name__)

class ServiceManager:
    """Manages all application services and their lifecycle."""
    
    def __init__(self, backend_port: int = 8000, frontend_port: int = 5173, skip_deps: bool = False):
        self.backend_port = backend_port
        self.frontend_port = frontend_port
        self.skip_deps = skip_deps
        self.processes: Dict[str, subprocess.Popen] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.running = True
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def check_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            # Check if the port is already in use by our application
            if port == self.backend_port:
                # Try to connect to the health endpoint
                if self.check_service_health(f"http://localhost:{port}/health"):
                    logger.info(f"✅ Port {port} is already in use by our backend service")
                    return True
            elif port == self.frontend_port:
                # Try to connect to the frontend
                try:
                    response = requests.get(f"http://localhost:{port}", timeout=2)
                    if response.status_code == 200:
                        logger.info(f"✅ Port {port} is already in use by our frontend service")
                        return True
                except requests.RequestException:
                    pass
            return False
    
    def check_service_health(self, url: str, timeout: int = 5) -> bool:
        """Check if a service is healthy by making a request."""
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def check_neo4j_connection(self) -> bool:
        """Check if Neo4j is running and accessible."""
        try:
            # Try to connect to Neo4j bolt port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                result = s.connect_ex(('localhost', 7687))
                return result == 0
        except Exception:
            return False
    
    def check_redis_connection(self) -> bool:
        """Check if Redis is running and accessible."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                result = s.connect_ex(('localhost', 6379))
                return result == 0
        except Exception:
            return False
    
    def start_neo4j(self) -> bool:
        """Start Neo4j database if not running."""
        if self.check_neo4j_connection():
            logger.info("✅ Neo4j is already running")
            return True
        
        if self.skip_deps:
            logger.warning("⚠️  Skipping Neo4j startup (--skip-deps flag)")
            return False
        
        logger.info("🚀 Starting Neo4j database...")
        
        # Check if Neo4j is installed
        try:
            # Try to start Neo4j using common installation paths
            neo4j_paths = [
                "/usr/local/bin/neo4j",
                "/opt/neo4j/bin/neo4j",
                "neo4j"  # If in PATH
            ]
            
            neo4j_cmd = None
            for path in neo4j_paths:
                try:
                    subprocess.run([path, "version"], capture_output=True, check=True)
                    neo4j_cmd = path
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            if neo4j_cmd:
                # Start Neo4j
                process = subprocess.Popen(
                    [neo4j_cmd, "start"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for Neo4j to start
                for _ in range(30):  # Wait up to 30 seconds
                    if self.check_neo4j_connection():
                        logger.info("✅ Neo4j started successfully")
                        return True
                    time.sleep(1)
                
                logger.error("❌ Failed to start Neo4j")
                return False
            else:
                logger.error("❌ Neo4j not found. Please install Neo4j first.")
                logger.info("💡 Installation instructions:")
                logger.info("   - Download from: https://neo4j.com/download/")
                logger.info("   - Or use Docker: docker run -p 7474:7474 -p 7687:7687 neo4j:latest")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting Neo4j: {e}")
            return False
    
    def start_redis(self) -> bool:
        """Start Redis server if not running."""
        if self.check_redis_connection():
            logger.info("✅ Redis is already running")
            return True
        
        if self.skip_deps:
            logger.warning("⚠️  Skipping Redis startup (--skip-deps flag)")
            return False
        
        logger.info("🚀 Starting Redis server...")
        
        try:
            # Try to start Redis
            redis_cmd = "redis-server"
            process = subprocess.Popen(
                [redis_cmd, "--daemonize", "yes"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for Redis to start
            for _ in range(10):  # Wait up to 10 seconds
                if self.check_redis_connection():
                    logger.info("✅ Redis started successfully")
                    return True
                time.sleep(1)
            
            logger.error("❌ Failed to start Redis")
            return False
            
        except FileNotFoundError:
            logger.error("❌ Redis not found. Please install Redis first.")
            logger.info("💡 Installation instructions:")
            logger.info("   - macOS: brew install redis")
            logger.info("   - Ubuntu: sudo apt-get install redis-server")
            logger.info("   - Or use Docker: docker run -p 6379:6379 redis:latest")
            return False
        except Exception as e:
            logger.error(f"❌ Error starting Redis: {e}")
            return False
    
    def setup_python_environment(self) -> bool:
        """Setup Python environment and check dependencies."""
        logger.info("🔧 Setting up Python environment...")
        
        # Use system Python instead of virtual environment
        python_path = sys.executable
        pip_path = "python3"  # Use python3 for pip commands
        
        # Check if core dependencies are installed
        try:
            result = subprocess.run(
                [python_path, "-c", "import fastapi, celery, neo4j, requests"],
                capture_output=True
            )
            if result.returncode != 0:
                logger.info("📦 Installing core Python dependencies...")
                subprocess.run([pip_path, "install", "fastapi", "celery", "neo4j", "requests", "uvicorn", "python-dotenv"], check=True)
                logger.info("✅ Core dependencies installed")
            else:
                logger.info("✅ Python dependencies already installed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
        
        return True
    
    def start_backend(self) -> bool:
        """Start the FastAPI backend server."""
        # Check if backend is already running
        if self.check_service_health(f"http://localhost:{self.backend_port}/health"):
            logger.info(f"✅ Backend server is already running on port {self.backend_port}")
            return True
        
        if not self.check_port_available(self.backend_port):
            logger.error(f"❌ Port {self.backend_port} is not available")
            return False
        
        logger.info(f"🚀 Starting backend server on port {self.backend_port}...")
        
        # Use system Python
        python_path = sys.executable
        
        try:
            # Start FastAPI server
            process = subprocess.Popen(
                [
                    python_path, "-m", "uvicorn", 
                    "backend.main:app", 
                    "--host", "0.0.0.0",
                    "--port", str(self.backend_port),
                    "--reload"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes['backend'] = process
            
            # Wait for backend to start
            for _ in range(30):  # Wait up to 30 seconds
                if self.check_service_health(f"http://localhost:{self.backend_port}/health"):
                    logger.info("✅ Backend server started successfully")
                    return True
                time.sleep(1)
            
            logger.error("❌ Failed to start backend server")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error starting backend: {e}")
            return False
    
    def start_celery_worker(self) -> bool:
        """Start Celery worker for background tasks."""
        logger.info("🚀 Starting Celery worker...")
        
        # Use system Python
        python_path = sys.executable
        
        try:
            # Start Celery worker
            process = subprocess.Popen(
                [
                    python_path, "-m", "celery", 
                    "-A", "backend.app.services.celery_service.app", 
                    "worker", 
                    "--loglevel=info",
                    "--concurrency=2"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()  # Ensure we're in the project root
            )
            
            self.processes['celery'] = process
            
            # Give Celery some time to start
            time.sleep(5)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info("✅ Celery worker started successfully")
                return True
            else:
                logger.error("❌ Celery worker failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting Celery worker: {e}")
            return False
    
    def start_frontend(self) -> bool:
        """Start the React frontend development server."""
        # Check if frontend is already running
        try:
            response = requests.get(f"http://localhost:{self.frontend_port}", timeout=2)
            if response.status_code == 200:
                logger.info(f"✅ Frontend server is already running on port {self.frontend_port}")
                return True
        except requests.RequestException:
            pass
        
        if not self.check_port_available(self.frontend_port):
            logger.error(f"❌ Port {self.frontend_port} is not available")
            return False
        
        logger.info(f"🚀 Starting frontend server on port {self.frontend_port}...")
        
        # Check if node_modules exists
        frontend_path = Path("frontend")
        if not frontend_path.exists():
            logger.error("❌ Frontend directory not found")
            return False
        
        # Check if node_modules exists
        node_modules_path = frontend_path / "node_modules"
        if not node_modules_path.exists():
            logger.info("📦 Installing frontend dependencies...")
            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=frontend_path,
                    check=True,
                    capture_output=True
                )
                logger.info("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install frontend dependencies: {e}")
                return False
        
        try:
            # Start frontend development server
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes['frontend'] = process
            
            # Wait for frontend to start
            for _ in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"http://localhost:{self.frontend_port}", timeout=5)
                    if response.status_code == 200:
                        logger.info("✅ Frontend server started successfully")
                        return True
                except requests.RequestException:
                    pass
                time.sleep(1)
            
            logger.error("❌ Failed to start frontend server")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error starting frontend: {e}")
            return False
    
    def monitor_services(self):
        """Monitor all services and restart if needed."""
        while self.running:
            try:
                # Check backend health
                if 'backend' in self.processes:
                    if not self.check_service_health(f"http://localhost:{self.backend_port}/health"):
                        logger.warning("⚠️  Backend server is not responding, restarting...")
                        self.restart_backend()
                
                # Check frontend health
                if 'frontend' in self.processes:
                    try:
                        response = requests.get(f"http://localhost:{self.frontend_port}", timeout=5)
                        if response.status_code != 200:
                            logger.warning("⚠️  Frontend server is not responding, restarting...")
                            self.restart_frontend()
                    except requests.RequestException:
                        logger.warning("⚠️  Frontend server is not responding, restarting...")
                        self.restart_frontend()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in service monitoring: {e}")
                time.sleep(30)
    
    def restart_backend(self):
        """Restart the backend server."""
        if 'backend' in self.processes:
            self.processes['backend'].terminate()
            time.sleep(2)
            self.start_backend()
    
    def restart_frontend(self):
        """Restart the frontend server."""
        if 'frontend' in self.processes:
            self.processes['frontend'].terminate()
            time.sleep(2)
            self.start_frontend()
    
    def cleanup(self):
        """Clean up all running processes."""
        logger.info("🧹 Cleaning up processes...")
        
        for name, process in self.processes.items():
            try:
                logger.info(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️  Force killing {name}...")
                process.kill()
            except Exception as e:
                logger.error(f"❌ Error stopping {name}: {e}")
        
        self.processes.clear()
        logger.info("✅ Cleanup completed")
    
    def start_all(self) -> bool:
        """Start all application services."""
        logger.info("🎯 Starting Finance Knowledge Graph Application...")
        
        # Setup Python environment
        if not self.setup_python_environment():
            return False
        
        # Start dependencies
        if not self.skip_deps:
            if not self.start_neo4j():
                return False
            if not self.start_redis():
                return False
        
        # Start backend services
        if not self.start_backend():
            return False
        
        if not self.start_celery_worker():
            return False
        
        # Start frontend
        if not self.start_frontend():
            return False
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
        monitor_thread.start()
        self.threads['monitor'] = monitor_thread
        
        logger.info("🎉 All services started successfully!")
        logger.info(f"📊 Backend API: http://localhost:{self.backend_port}")
        logger.info(f"📊 Frontend: http://localhost:{self.frontend_port}")
        logger.info(f"📊 API Docs: http://localhost:{self.backend_port}/docs")
        logger.info("🛑 Press Ctrl+C to stop all services")
        
        return True
    
    def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested...")
            self.running = False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start Finance Knowledge Graph Application")
    parser.add_argument("--port-backend", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--port-frontend", type=int, default=5173, help="Frontend port (default: 5173)")
    parser.add_argument("--skip-deps", action="store_true", help="Skip starting dependencies (Neo4j, Redis)")
    
    args = parser.parse_args()
    
    # Create service manager
    manager = ServiceManager(
        backend_port=args.port_backend,
        frontend_port=args.port_frontend,
        skip_deps=args.skip_deps
    )
    
    # Start all services
    if manager.start_all():
        # Wait for shutdown
        manager.wait_for_shutdown()
    else:
        logger.error("❌ Failed to start application")
        sys.exit(1)

if __name__ == "__main__":
    main() 