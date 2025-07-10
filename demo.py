#!/usr/bin/env python3
"""
Finance Knowledge Graph - Demo Script
Demonstrates all the new features implemented
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_FILE = "backend/test_files/test.pdf"

def print_section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def test_health():
    """Test basic health endpoint"""
    print_section("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_success("Backend is healthy")
            print(f"Response: {response.json()}")
        else:
            print_error(f"Health check failed: {response.status_code}")
    except Exception as e:
        print_error(f"Health check error: {e}")

def test_upload():
    """Test document upload"""
    print_section("Document Upload")
    try:
        if not Path(TEST_FILE).exists():
            print_error(f"Test file not found: {TEST_FILE}")
            return None
            
        with open(TEST_FILE, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/api/v1/upload", files=files)
            
        if response.status_code == 200:
            data = response.json()
            print_success("Document uploaded successfully")
            print(f"Document ID: {data['document_id']}")
            return data['document_id']
        else:
            print_error(f"Upload failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Upload error: {e}")
        return None

def test_validation(document_id):
    """Test document validation"""
    print_section("Document Validation")
    try:
        payload = {
            "document_id": document_id,
            "rules": []
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{document_id}/validate",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Document validation completed")
            print(f"Results: {data['summary']}")
            return data
        else:
            print_error(f"Validation failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Validation error: {e}")
        return None

def test_processing(document_id):
    """Test document processing"""
    print_section("Document Processing")
    try:
        payload = {
            "extract_entities": True,
            "extract_relationships": True,
            "build_graph": True
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/{document_id}/process",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Document processing completed")
            print(f"Processing time: {data['processing_time']}s")
            print(f"Entities: {len(data['entities'])}")
            print(f"Relationships: {len(data['relationships'])}")
            return data
        else:
            print_error(f"Processing failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Processing error: {e}")
        return None

def test_graph_visualization(document_id):
    """Test graph visualization"""
    print_section("Graph Visualization")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/graph/{document_id}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Graph data retrieved")
            print(f"Nodes: {data['metadata']['total_nodes']}")
            print(f"Edges: {data['metadata']['total_edges']}")
            return data
        else:
            print_error(f"Graph retrieval failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Graph error: {e}")
        return None

def test_validation_rules():
    """Test validation rules management"""
    print_section("Validation Rules")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/validation/rules")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Validation rules retrieved")
            print(f"Available rules: {len(data['rules'])}")
            for rule in data['rules']:
                print(f"  - {rule['name']}: {rule['description']}")
            return data
        else:
            print_error(f"Rules retrieval failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Rules error: {e}")
        return None

def test_corrections(document_id):
    """Test correction management"""
    print_section("Correction Management")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents/{document_id}/corrections")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Corrections retrieved")
            print(f"Corrections: {len(data['corrections'])}")
            return data
        else:
            print_error(f"Corrections retrieval failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Corrections error: {e}")
        return None

def main():
    """Run the complete demo"""
    print("🚀 Finance Knowledge Graph - Feature Demo")
    print("=" * 60)
    
    # Test all features
    test_health()
    
    document_id = test_upload()
    if document_id:
        test_validation(document_id)
        test_processing(document_id)
        test_graph_visualization(document_id)
        test_corrections(document_id)
    
    test_validation_rules()
    
    print_section("Demo Complete")
    print("🎉 All features have been tested!")
    print("\nNext steps:")
    print("1. Open http://localhost:5173 in your browser")
    print("2. Upload a document and explore the features")
    print("3. Check out the graph visualization")
    print("4. Try the validation and correction features")

if __name__ == "__main__":
    main() 