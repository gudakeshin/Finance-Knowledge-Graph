#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.document_processing import DocumentProcessor
from backend.app.services.entity_recognition import FinancialEntityRecognizer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extraction():
    """Test the extraction pipeline step by step"""
    
    print("=== Testing Document Extraction Pipeline ===\n")
    
    # Initialize services
    print("1. Initializing services...")
    try:
        document_processor = DocumentProcessor()
        entity_recognizer = FinancialEntityRecognizer()
        print("✅ Services initialized successfully")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return
    
    # Test with a sample text
    print("\n2. Testing with sample text...")
    sample_text = """
    INVOICE
    
    Invoice Number: INV-2024-001
    Date: January 15, 2024
    Due Date: February 15, 2024
    
    Bill To:
    John Doe
    ABC Corporation
    123 Main Street
    New York, NY 10001
    
    From:
    XYZ Consulting Services
    456 Business Ave
    San Francisco, CA 94102
    
    Description:
    - Consulting Services: $5,000.00
    - Project Management: $2,500.00
    - Technical Support: $1,000.00
    
    Subtotal: $8,500.00
    Tax (8.5%): $722.50
    Total Amount: $9,222.50
    
    Payment Terms: Net 30
    """
    
    print(f"Sample text length: {len(sample_text)} characters")
    print(f"Sample text preview: {sample_text[:200]}...")
    
    # Extract entities
    print("\n3. Extracting entities...")
    try:
        entities = entity_recognizer.extract_entities(sample_text)
        print(f"✅ Extracted {len(entities)} entities")
        
        for i, entity in enumerate(entities[:10]):  # Show first 10
            print(f"  {i+1}. {entity.text} ({entity.type}) - Confidence: {entity.confidence:.2f}")
            
    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
        return
    
    # Test with a real file if available
    print("\n4. Testing with real file...")
    test_files = [
        "data/test_files/test.pdf",
        "data/test_files/Cost-Accounting.pdf",
        "backend/test_files/test.pdf",
        "backend/test_files/Cost-Accounting.pdf"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"Found test file: {test_file}")
            try:
                extracted_text = document_processor.extract_text(test_file)
                print(f"✅ Extracted {len(extracted_text)} characters from {test_file}")
                print(f"Text preview: {extracted_text[:300]}...")
                
                # Extract entities from real file
                entities = entity_recognizer.extract_entities(extracted_text)
                print(f"✅ Extracted {len(entities)} entities from real file")
                
                for i, entity in enumerate(entities[:5]):  # Show first 5
                    print(f"  {i+1}. {entity.text} ({entity.type}) - Confidence: {entity.confidence:.2f}")
                
                break
                
            except Exception as e:
                print(f"❌ Failed to process {test_file}: {e}")
                continue
    else:
        print("No test files found")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_extraction() 