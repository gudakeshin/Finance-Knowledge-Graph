#!/usr/bin/env python3
"""
Test script for the Finance Knowledge Graph startup process.
This script tests the startup functionality without actually starting services.
"""

import os
import sys
import subprocess
import socket
import requests
from pathlib import Path
from typing import Dict, List, Tuple

def test_port_availability(port: int) -> bool:
    """Test if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def test_python_environment() -> Dict[str, bool]:
    """Test Python environment setup."""
    results = {}
    
    # Check Python version
    try:
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True, check=True)
        results['python_version'] = True
        print(f"✅ Python version: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        results['python_version'] = False
        print("❌ Python version check failed")
    
    # Check if venv exists
    venv_path = Path("venv")
    results['venv_exists'] = venv_path.exists()
    if results['venv_exists']:
        print("✅ Virtual environment exists")
    else:
        print("⚠️  Virtual environment not found (will be created)")
    
    # Check if requirements.txt exists
    requirements_path = Path("requirements.txt")
    results['requirements_exists'] = requirements_path.exists()
    if results['requirements_exists']:
        print("✅ requirements.txt exists")
    else:
        print("❌ requirements.txt not found")
    
    return results

def test_frontend_environment() -> Dict[str, bool]:
    """Test frontend environment setup."""
    results = {}
    
    # Check if frontend directory exists
    frontend_path = Path("frontend")
    results['frontend_exists'] = frontend_path.exists()
    if results['frontend_exists']:
        print("✅ Frontend directory exists")
    else:
        print("❌ Frontend directory not found")
        return results
    
    # Check package.json
    package_json = frontend_path / "package.json"
    results['package_json_exists'] = package_json.exists()
    if results['package_json_exists']:
        print("✅ package.json exists")
    else:
        print("❌ package.json not found")
    
    # Check node_modules
    node_modules = frontend_path / "node_modules"
    results['node_modules_exists'] = node_modules.exists()
    if results['node_modules_exists']:
        print("✅ node_modules exists")
    else:
        print("⚠️  node_modules not found (will be installed)")
    
    return results

def test_dependencies() -> Dict[str, bool]:
    """Test if dependencies are available."""
    results = {}
    
    # Test Neo4j
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(('localhost', 7687))
            results['neo4j_running'] = result == 0
            if results['neo4j_running']:
                print("✅ Neo4j is running")
            else:
                print("⚠️  Neo4j is not running (will be started if available)")
    except Exception:
        results['neo4j_running'] = False
        print("⚠️  Neo4j connection test failed")
    
    # Test Redis
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(('localhost', 6379))
            results['redis_running'] = result == 0
            if results['redis_running']:
                print("✅ Redis is running")
            else:
                print("⚠️  Redis is not running (will be started if available)")
    except Exception:
        results['redis_running'] = False
        print("⚠️  Redis connection test failed")
    
    return results

def test_backend_files() -> Dict[str, bool]:
    """Test if backend files exist."""
    results = {}
    
    # Check main.py
    main_py = Path("backend/main.py")
    results['main_py_exists'] = main_py.exists()
    if results['main_py_exists']:
        print("✅ backend/main.py exists")
    else:
        print("❌ backend/main.py not found")
    
    # Check celery service
    celery_service = Path("backend/app/services/celery_service.py")
    results['celery_service_exists'] = celery_service.exists()
    if results['celery_service_exists']:
        print("✅ Celery service exists")
    else:
        print("❌ Celery service not found")
    
    # Check routers
    routers_dir = Path("backend/routers")
    results['routers_exist'] = routers_dir.exists() and any(routers_dir.iterdir())
    if results['routers_exist']:
        print("✅ Backend routers exist")
    else:
        print("❌ Backend routers not found")
    
    return results

def test_startup_script() -> Dict[str, bool]:
    """Test if startup script exists and is executable."""
    results = {}
    
    # Check startup script
    startup_script = Path("start_app.py")
    results['startup_script_exists'] = startup_script.exists()
    if results['startup_script_exists']:
        print("✅ start_app.py exists")
    else:
        print("❌ start_app.py not found")
    
    # Check shell script
    shell_script = Path("start.sh")
    results['shell_script_exists'] = shell_script.exists()
    if results['shell_script_exists']:
        print("✅ start.sh exists")
    else:
        print("❌ start.sh not found")
    
    # Check if shell script is executable
    if results['shell_script_exists']:
        results['shell_script_executable'] = os.access(shell_script, os.X_OK)
        if results['shell_script_executable']:
            print("✅ start.sh is executable")
        else:
            print("⚠️  start.sh is not executable")
    
    return results

def test_ports() -> Dict[str, bool]:
    """Test if required ports are available."""
    results = {}
    
    # Test backend port
    backend_port = 8000
    results['backend_port_available'] = test_port_availability(backend_port)
    if results['backend_port_available']:
        print(f"✅ Port {backend_port} (backend) is available")
    else:
        print(f"❌ Port {backend_port} (backend) is not available")
    
    # Test frontend port
    frontend_port = 5173
    results['frontend_port_available'] = test_port_availability(frontend_port)
    if results['frontend_port_available']:
        print(f"✅ Port {frontend_port} (frontend) is available")
    else:
        print(f"❌ Port {frontend_port} (frontend) is not available")
    
    return results

def run_comprehensive_test():
    """Run all tests and provide a summary."""
    print("🧪 Running Finance Knowledge Graph Startup Tests")
    print("=" * 50)
    
    all_results = {}
    
    # Test Python environment
    print("\n📦 Testing Python Environment:")
    all_results['python'] = test_python_environment()
    
    # Test frontend environment
    print("\n🎨 Testing Frontend Environment:")
    all_results['frontend'] = test_frontend_environment()
    
    # Test dependencies
    print("\n🔧 Testing Dependencies:")
    all_results['dependencies'] = test_dependencies()
    
    # Test backend files
    print("\n⚙️  Testing Backend Files:")
    all_results['backend'] = test_backend_files()
    
    # Test startup scripts
    print("\n🚀 Testing Startup Scripts:")
    all_results['startup'] = test_startup_script()
    
    # Test ports
    print("\n🔌 Testing Port Availability:")
    all_results['ports'] = test_ports()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        print(f"\n{category.upper()}:")
        for test_name, result in results.items():
            total_tests += 1
            if result:
                passed_tests += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            print(f"  {test_name}: {status}")
    
    print(f"\n📈 RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The application should start successfully.")
        print("\n💡 To start the application, run:")
        print("   ./start.sh")
        print("   or")
        print("   python3 start_app.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues before starting the application.")
        print("\n💡 Common fixes:")
        print("   - Install missing dependencies")
        print("   - Free up occupied ports")
        print("   - Ensure all required files exist")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1) 