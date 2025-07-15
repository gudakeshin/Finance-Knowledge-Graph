import json
import logging
import subprocess
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    # Core financial document types
    INVOICE = "invoice"
    RECEIPT = "receipt"
    BANK_STATEMENT = "bank_statement"
    FINANCIAL_REPORT = "financial_report"
    CONTRACT = "contract"
    TAX_DOCUMENT = "tax_document"
    INSURANCE_POLICY = "insurance_policy"
    LOAN_AGREEMENT = "loan_agreement"
    
    # Business document types
    BUSINESS_PLAN = "business_plan"
    MARKETING_MATERIAL = "marketing_material"
    RESEARCH_REPORT = "research_report"
    WHITE_PAPER = "white_paper"
    PRESENTATION = "presentation"
    MEMO = "memo"
    LETTER = "letter"
    
    # Dynamic types
    CUSTOM = "custom"
    UNKNOWN = "unknown"

@dataclass
class DocumentSchema:
    name: str
    document_type: DocumentType
    fields: List[Dict[str, Any]]
    confidence: float
    description: str
    custom_type: Optional[str] = None

class IntelligentDocumentClassifier:
    def __init__(self, model_name: str = "deepseek-r1:1.5b"):
        self.model_name = model_name
        
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama with the given prompt and return the response."""
        try:
            # Prepare the command
            cmd = [
                "ollama", "run", self.model_name,
                prompt
            ]
            
            # Execute the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Ollama error: {result.stderr}")
                return ""
                
        except subprocess.TimeoutExpired:
            logger.error("Ollama request timed out")
            return ""
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return ""

    def analyze_document_content(self, text: str, entities: List) -> Tuple[DocumentType, float, str, Dict]:
        """
        Intelligently analyze document content and determine:
        1. Document type (including custom types)
        2. Confidence level
        3. Reasoning
        4. Suggested schema fields based on content
        """
        # Convert entities to JSON-serializable format
        entities_dict = []
        for entity in entities[:15]:  # Use more entities for better analysis
            if hasattr(entity, 'to_dict'):
                entities_dict.append(entity.to_dict())
            else:
                entities_dict.append({
                    "text": getattr(entity, 'text', str(entity)),
                    "type": getattr(entity, 'type', 'unknown'),
                    "confidence": getattr(entity, 'confidence', 0.0)
                })

        prompt = f"""
You are an expert document analyst specializing in financial and business documents. Your task is to analyze the document content and provide a definitive classification.

Document text (first 2000 characters):
{text[:2000]}

Extracted entities:
{json.dumps(entities_dict, indent=2)}

CRITICAL INSTRUCTIONS:
1. You MUST classify this document into one of the available types or provide a specific custom type. NEVER return 'unknown'.
2. If the document doesn't fit standard types, you MUST invent a descriptive custom type name based on the content (e.g. 'business_analysis', 'cfo_strategy', 'market_research', etc.).
3. You MUST provide a confidence score between 0.7 and 1.0 (be confident in your analysis)
4. If you return 'unknown', your answer will be discarded and you will be penalized.
5. Always suggest relevant fields based on the actual content found

Available standard types (choose the closest match):
- invoice: Business invoice with vendor, amounts, payment terms
- receipt: Purchase receipt with merchant, items, transaction details  
- bank_statement: Bank account statement with transactions, balances
- financial_report: Financial performance report with metrics, analysis
- contract: Legal contract with parties, terms, obligations
- tax_document: Tax-related document with financial information
- insurance_policy: Insurance policy with coverage, terms
- loan_agreement: Loan document with terms, amounts, parties
- business_plan: Business strategy and planning document
- marketing_material: Marketing and promotional content
- research_report: Research findings and analysis
- white_paper: Technical or business white paper
- presentation: Presentation or slide deck content
- memo: Internal memorandum or communication
- letter: Business or formal letter

ANALYSIS REQUIREMENTS:
- If document type is 'custom', you MUST provide a specific custom_type_name (never leave it blank)
- Analyze the actual content and suggest fields that would be useful for data extraction
- Focus on fields that appear in the document text or entities
- Provide realistic examples based on the content

Respond with ONLY valid JSON in this exact format:
{{
    "document_type": "specific_type_or_custom",
    "custom_type_name": "descriptive_name_if_custom",
    "confidence": 0.85,
    "reasoning": "Clear explanation of why this classification was chosen",
    "content_analysis": {{
        "primary_purpose": "What is the main purpose of this document?",
        "target_audience": "Who is this document for?",
        "key_topics": ["topic1", "topic2", "topic3"],
        "document_structure": "How is the information organized?"
    }},
    "suggested_fields": [
        {{
            "name": "Summary of Extracted Document",
            "key": "document_summary",
            "required": true,
            "description": "Summary of the main content and key points from the document",
            "examples": ["Document discusses CFO role in financial strategy", "Guide for developing micro-applications"]
        }}
    ],
    "schema_description": "Comprehensive description of what this document contains"
}}

IMPORTANT: Only respond with valid JSON. No commentary, tags, or markdown. If you return 'unknown', your answer will be discarded and you will be penalized.
"""

        response = self._call_ollama(prompt)
        
        def extract_json_block(text):
            # Find the first {...} block in the text, handling nested braces
            import re
            brace_count = 0
            start = -1
            for i, char in enumerate(text):
                if char == '{':
                    if start == -1:
                        start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if start != -1 and brace_count == 0:
                        json_block = text[start:i+1]
                        # Clean up common JSON formatting issues
                        json_block = re.sub(r',\s*}', '}', json_block)  # Remove trailing commas
                        json_block = re.sub(r',\s*]', ']', json_block)  # Remove trailing commas in arrays
                        return json_block
            return None

        try:
            if response and response.strip():
                response = response.strip()
                # Try to extract the first JSON block
                json_block = extract_json_block(response)
                if not json_block:
                    logger.error(f"No JSON block found in LLM response: {response}")
                    raise ValueError("No JSON block found")
                if response != json_block:
                    logger.warning(f"LLM response contained extra text. Extracted JSON block for parsing.")
                result = json.loads(json_block)
                # Determine document type
                doc_type_str = result.get("document_type", "unknown")
                confidence = float(result.get("confidence", 0.0))
                custom_type = result.get("custom_type_name", "")

                # Fallback: If LLM returns 'unknown' or blank custom_type, generate a custom type
                if doc_type_str == "unknown" or (doc_type_str == "custom" and not custom_type.strip()):
                    # Try to use the most common entity type or a phrase from the document
                    from collections import Counter
                    entity_types = [e.get('type') for e in entities_dict if 'type' in e]
                    most_common_type = None
                    if entity_types:
                        most_common_type = Counter(entity_types).most_common(1)[0][0].lower()
                    # Use first 3 words of the document as a fallback
                    first_words = '_'.join(text.strip().split()[:3]).lower() if text.strip() else "custom_document"
                    generated_type = most_common_type or first_words or "custom_document"
                    doc_type_str = "custom"
                    custom_type = generated_type
                    logger.info(f"[Fallback] Generated custom type: {custom_type}")
                    result["document_type"] = "custom"
                    result["custom_type_name"] = custom_type
                    confidence = max(confidence, 0.7)

                if doc_type_str == "custom":
                    doc_type = DocumentType.CUSTOM
                else:
                    try:
                        doc_type = DocumentType(doc_type_str)
                        custom_type = None
                    except ValueError:
                        doc_type = DocumentType.CUSTOM
                        custom_type = doc_type_str
                        logger.info(f"Unknown document type '{doc_type_str}', treating as custom: {custom_type}")
                reasoning = result.get("reasoning", "No reasoning provided")
                logger.info(f"Intelligent analysis classified document as: {doc_type.value} (confidence: {confidence})")
                if custom_type:
                    logger.info(f"Custom type: {custom_type}")
                logger.info(f"Reasoning: {reasoning}")
                return doc_type, confidence, reasoning, result
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse LLM analysis response: {e}")
            logger.error(f"Raw response: {response}")
        # Fallback to unknown
        return DocumentType.UNKNOWN, 0.0, "Failed to analyze document", {}

    def create_dynamic_schema(self, analysis_result: Dict) -> DocumentSchema:
        """
        Create a dynamic schema based on the intelligent analysis.
        """
        doc_type_str = analysis_result.get("document_type", "unknown")
        custom_type = analysis_result.get("custom_type_name")
        
        if doc_type_str == "custom":
            doc_type = DocumentType.CUSTOM
            schema_name = f"{custom_type.title()} Schema" if custom_type else "Custom Document Schema"
        else:
            try:
                doc_type = DocumentType(doc_type_str)
                schema_name = f"{doc_type_str.title().replace('_', ' ')} Schema"
            except ValueError:
                doc_type = DocumentType.CUSTOM
                schema_name = f"{doc_type_str.title()} Schema"
        
        # Get suggested fields from analysis
        suggested_fields = analysis_result.get("suggested_fields", [])
        
        # Add some common fields that are often useful
        common_fields = [
            {"name": "Document Type", "key": "document_type", "required": True, "description": "Type of document"},
            {"name": "Date", "key": "date", "required": False, "description": "Document date"},
            {"name": "Title", "key": "title", "required": False, "description": "Document title"},
            {"name": "Author/Company", "key": "author", "required": False, "description": "Document author or company"}
        ]
        
        # Combine suggested fields with common fields, avoiding duplicates
        all_fields = []
        field_keys = set()
        
        # Add suggested fields first
        for field in suggested_fields:
            key = field.get("key", field.get("name", "").lower().replace(" ", "_"))
            if key not in field_keys:
                all_fields.append(field)
                field_keys.add(key)
        
        # Add common fields that weren't already included
        for field in common_fields:
            key = field.get("key")
            if key not in field_keys:
                all_fields.append(field)
                field_keys.add(key)
        
        confidence = float(analysis_result.get("confidence", 0.0))
        description = analysis_result.get("schema_description", f"Dynamic schema for {doc_type.value} documents")
        
        return DocumentSchema(
            name=schema_name,
            document_type=doc_type,
            fields=all_fields,
            confidence=confidence,
            description=description,
            custom_type=custom_type
        )

    def classify_and_schema_document(self, text: str, entities: List) -> Tuple[DocumentType, DocumentSchema, float, str]:
        """
        Main method to classify document and create appropriate schema.
        """
        # Analyze document content
        doc_type, confidence, reasoning, analysis_result = self.analyze_document_content(text, entities)
        
        # Create dynamic schema based on analysis
        schema = self.create_dynamic_schema(analysis_result)
        
        return doc_type, schema, confidence, reasoning

    def get_available_document_types(self) -> List[Dict[str, Any]]:
        """Get list of available document types for API endpoint."""
        types = []
        for doc_type in DocumentType:
            if doc_type != DocumentType.CUSTOM:
                types.append({
                    "type": doc_type.value,
                    "name": doc_type.value.replace("_", " ").title(),
                    "description": f"Standard {doc_type.value.replace('_', ' ')} document"
                })
        
        # Add custom type option
        types.append({
            "type": "custom",
            "name": "Custom Document",
            "description": "Dynamically classified document type"
        })
        
        return types 