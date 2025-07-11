#!/usr/bin/env python3
"""
Finance Knowledge Graph - Application Stop Script

This script gracefully stops all running services for the Finance Knowledge Graph application:
- FastAPI backend server
- React frontend development server  
- Celery worker processes
- Redis server (if started by our app)
- Neo4j database (if started by our app)

Usage:
    python stop_app.py [options]

Options:
    --all              Stop all services (default)
    --backend          Stop only backend server
    --frontend         Stop only frontend server
    --celery           Stop only Celery worker
    --infra            Stop only infrastructure (Redis, Neo4j)
    --force            Force kill processes (not graceful)
    --dry-run          Show what would be stopped without actually stopping
"""

import os
import sys
import signal
import subprocess
import psutil
import argparse
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AppStopper:
    """Manages stopping of all application services."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_port = 8000
        self.frontend_port = 5173
        self.celery_port = 6379  # Redis port
        self.neo4j_port = 7474
        
        # Process patterns to identify our services
        self.service_patterns = {
            'backend': [
                'uvicorn',
                'python.*main.py',
                'python.*start_app.py'
            ],
            'frontend': [
                'vite',
                'npm.*dev',
                'node.*vite'
            ],
            'celery': [
                'celery.*worker',
                'python.*celery'
            ],
            'redis': [
                'redis-server',
                'redis.*6379'
            ],
            'neo4j': [
                'neo4j',
                'java.*neo4j'
            ]
        }
        
        # PIDs of processes we started (if available)
        self.started_pids = self._load_started_pids()
    
    def _load_started_pids(self) -> Dict[str, List[int]]:
        """Load PIDs of processes we started from a file."""
        pid_file = self.project_root / '.started_pids'
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pids = {}
                    for line in f:
                        if ':' in line:
                            service, pid_list = line.strip().split(':', 1)
                            pids[service] = [int(pid) for pid in pid_list.split(',') if pid.isdigit()]
                    return pids
            except Exception as e:
                logger.warning(f"Could not load PID file: {e}")
        return {}
    
    def _save_started_pids(self):
        """Save current PIDs to file."""
        pid_file = self.project_root / '.started_pids'
        try:
            with open(pid_file, 'w') as f:
                for service, pids in self.started_pids.items():
                    if pids:
                        f.write(f"{service}:{','.join(map(str, pids))}\n")
        except Exception as e:
            logger.warning(f"Could not save PID file: {e}")
    
    def find_processes_by_port(self, port: int) -> List[psutil.Process]:
        """Find processes using a specific port."""
        processes = []
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        process = psutil.Process(conn.pid)
                        processes.append(process)
                    except psutil.NoSuchProcess:
                        continue
        except Exception as e:
            logger.warning(f"Error finding processes on port {port}: {e}")
        return processes
    
    def find_processes_by_pattern(self, patterns: List[str]) -> List[psutil.Process]:
        """Find processes matching command patterns."""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    for pattern in patterns:
                        if pattern.lower() in cmdline.lower():
                            processes.append(proc)
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"Error finding processes by pattern: {e}")
        return processes
    
    def stop_processes(self, processes: List[psutil.Process], force: bool = False) -> bool:
        """Stop a list of processes gracefully or forcefully."""
        if not processes:
            return True
            
        success = True
        for proc in processes:
            try:
                if force:
                    logger.info(f"Force killing process {proc.pid} ({proc.name()})")
                    proc.kill()
                else:
                    logger.info(f"Gracefully stopping process {proc.pid} ({proc.name()})")
                    proc.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        proc.wait(timeout=10)
                        logger.info(f"✅ Process {proc.pid} stopped gracefully")
                    except psutil.TimeoutExpired:
                        logger.warning(f"⚠️  Process {proc.pid} didn't stop gracefully, force killing")
                        proc.kill()
                        proc.wait()
                        
            except psutil.NoSuchProcess:
                logger.info(f"Process {proc.pid} already stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping process {proc.pid}: {e}")
                success = False
                
        return success
    
    def stop_backend(self, force: bool = False) -> bool:
        """Stop the FastAPI backend server."""
        logger.info("🛑 Stopping backend server...")
        
        # Find processes by port
        port_processes = self.find_processes_by_port(self.backend_port)
        
        # Find processes by pattern
        pattern_processes = self.find_processes_by_pattern(self.service_patterns['backend'])
        
        # Combine and deduplicate
        all_processes = list(set(port_processes + pattern_processes))
        
        if not all_processes:
            logger.info("ℹ️  No backend processes found")
            return True
            
        logger.info(f"Found {len(all_processes)} backend process(es)")
        return self.stop_processes(all_processes, force)
    
    def stop_frontend(self, force: bool = False) -> bool:
        """Stop the React frontend development server."""
        logger.info("🛑 Stopping frontend server...")
        
        # Find processes by port
        port_processes = self.find_processes_by_port(self.frontend_port)
        
        # Find processes by pattern
        pattern_processes = self.find_processes_by_pattern(self.service_patterns['frontend'])
        
        # Combine and deduplicate
        all_processes = list(set(port_processes + pattern_processes))
        
        if not all_processes:
            logger.info("ℹ️  No frontend processes found")
            return True
            
        logger.info(f"Found {len(all_processes)} frontend process(es)")
        return self.stop_processes(all_processes, force)
    
    def stop_celery(self, force: bool = False) -> bool:
        """Stop Celery worker processes."""
        logger.info("🛑 Stopping Celery workers...")
        
        # Find processes by pattern
        processes = self.find_processes_by_pattern(self.service_patterns['celery'])
        
        if not processes:
            logger.info("ℹ️  No Celery processes found")
            return True
            
        logger.info(f"Found {len(processes)} Celery process(es)")
        return self.stop_processes(processes, force)
    
    def stop_infrastructure(self, force: bool = False) -> bool:
        """Stop infrastructure services (Redis, Neo4j)."""
        logger.info("🛑 Stopping infrastructure services...")
        
        success = True
        
        # Stop Redis
        redis_processes = self.find_processes_by_pattern(self.service_patterns['redis'])
        if redis_processes:
            logger.info(f"Found {len(redis_processes)} Redis process(es)")
            success &= self.stop_processes(redis_processes, force)
        else:
            logger.info("ℹ️  No Redis processes found")
        
        # Stop Neo4j
        neo4j_processes = self.find_processes_by_pattern(self.service_patterns['neo4j'])
        if neo4j_processes:
            logger.info(f"Found {len(neo4j_processes)} Neo4j process(es)")
            success &= self.stop_processes(neo4j_processes, force)
        else:
            logger.info("ℹ️  No Neo4j processes found")
        
        return success
    
    def stop_all(self, force: bool = False) -> bool:
        """Stop all application services."""
        logger.info("🛑 Stopping all Finance Knowledge Graph services...")
        
        success = True
        
        # Stop in reverse order of dependency
        success &= self.stop_frontend(force)
        success &= self.stop_backend(force)
        success &= self.stop_celery(force)
        success &= self.stop_infrastructure(force)
        
        # Clear PID file
        pid_file = self.project_root / '.started_pids'
        if pid_file.exists():
            try:
                pid_file.unlink()
                logger.info("🗑️  Cleared PID tracking file")
            except Exception as e:
                logger.warning(f"Could not clear PID file: {e}")
        
        return success
    
    def check_ports(self) -> Dict[str, bool]:
        """Check which ports are still in use."""
        ports = {
            'backend': self.backend_port,
            'frontend': self.frontend_port,
            'redis': self.celery_port,
            'neo4j': self.neo4j_port
        }
        
        status = {}
        for service, port in ports.items():
            processes = self.find_processes_by_port(port)
            status[service] = len(processes) > 0
            
        return status
    
    def show_status(self):
        """Show current status of all services."""
        logger.info("📊 Current service status:")
        
        port_status = self.check_ports()
        for service, in_use in port_status.items():
            status = "🟢 Running" if in_use else "🔴 Stopped"
            logger.info(f"  {service.capitalize()}: {status}")
        
        # Check for running processes
        for service, patterns in self.service_patterns.items():
            processes = self.find_processes_by_pattern(patterns)
            if processes:
                logger.info(f"  {service.capitalize()} processes: {len(processes)} found")
            else:
                logger.info(f"  {service.capitalize()} processes: None found")

def main():
    parser = argparse.ArgumentParser(
        description="Stop Finance Knowledge Graph application services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--all', 
        action='store_true', 
        help='Stop all services (default)'
    )
    parser.add_argument(
        '--backend', 
        action='store_true', 
        help='Stop only backend server'
    )
    parser.add_argument(
        '--frontend', 
        action='store_true', 
        help='Stop only frontend server'
    )
    parser.add_argument(
        '--celery', 
        action='store_true', 
        help='Stop only Celery worker'
    )
    parser.add_argument(
        '--infra', 
        action='store_true', 
        help='Stop only infrastructure (Redis, Neo4j)'
    )
    parser.add_argument(
        '--force', 
        action='store_true', 
        help='Force kill processes (not graceful)'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Show what would be stopped without actually stopping'
    )
    parser.add_argument(
        '--status', 
        action='store_true', 
        help='Show current status of all services'
    )
    
    args = parser.parse_args()
    
    stopper = AppStopper()
    
    if args.status:
        stopper.show_status()
        return
    
    if args.dry_run:
        logger.info("🔍 DRY RUN - Would stop the following:")
        stopper.show_status()
        return
    
    # Determine what to stop
    stop_backend = args.backend or args.all or not any([args.frontend, args.celery, args.infra])
    stop_frontend = args.frontend or args.all or not any([args.backend, args.celery, args.infra])
    stop_celery = args.celery or args.all or not any([args.backend, args.frontend, args.infra])
    stop_infra = args.infra or args.all or not any([args.backend, args.frontend, args.celery])
    
    success = True
    
    try:
        if stop_all := (args.all or not any([args.backend, args.frontend, args.celery, args.infra])):
            success = stopper.stop_all(args.force)
        else:
            if stop_frontend:
                success &= stopper.stop_frontend(args.force)
            if stop_backend:
                success &= stopper.stop_backend(args.force)
            if stop_celery:
                success &= stopper.stop_celery(args.force)
            if stop_infra:
                success &= stopper.stop_infrastructure(args.force)
        
        if success:
            logger.info("✅ All requested services stopped successfully")
            stopper.show_status()
        else:
            logger.error("❌ Some services failed to stop")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Stopping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 