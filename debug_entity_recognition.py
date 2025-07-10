#!/usr/bin/env python3

import sys
import os
sys.path.append('backend')

import fitz  # PyMuPDF
from app.services.entity_recognition import FinancialEntityRecognizer
from app.services.relationship_extraction import RelationshipExtractor

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file using PyMuPDF"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {str(e)}")
        return ""

def test_entity_recognition():
    # Test with a sample document
    doc_path = "data/0515ab2a-0909-409f-939c-57f1f96fa6f5/test.pdf"
    
    print("=== Testing Text Extraction ===")
    text = extract_text_from_pdf(doc_path)
    print(f"Extracted text length: {len(text)}")
    print(f"First 500 characters: {text[:500]}")
    
    if not text:
        print("No text extracted! This is the problem.")
        return
    
    print("\n=== Testing Entity Recognition ===")
    entity_recognizer = FinancialEntityRecognizer()
    entities = entity_recognizer.extract_entities(text)
    print(f"Found {len(entities)} entities")
    
    for i, entity in enumerate(entities[:10]):  # Show first 10 entities
        print(f"Entity {i+1}: {entity.text} (Type: {entity.type}, Confidence: {entity.confidence})")
    
    print("\n=== Testing Relationship Extraction ===")
    if entities:
        relationship_extractor = RelationshipExtractor()
        relationships = relationship_extractor.extract_relationships(text, entities)
        print(f"Found {len(relationships)} relationships")
        
        for i, rel in enumerate(relationships[:5]):  # Show first 5 relationships
            print(f"Relationship {i+1}: {rel.source_id} -> {rel.target_id} (Type: {rel.type})")
    else:
        print("No entities found, skipping relationship extraction")

if __name__ == "__main__":
    test_entity_recognition() 