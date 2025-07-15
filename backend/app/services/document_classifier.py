from typing import Dict, List, Any, Optional, Tuple
import re
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    BANK_STATEMENT = "bank_statement"
    FINANCIAL_REPORT = "financial_report"
    CONTRACT = "contract"
    TAX_DOCUMENT = "tax_document"
    INSURANCE_POLICY = "insurance_policy"
    LOAN_AGREEMENT = "loan_agreement"
    INVOICE_RECEIPT = "invoice_receipt"
    UNKNOWN = "unknown"

@dataclass
class DocumentSchema:
    name: str
    document_type: DocumentType
    fields: List[Dict[str, Any]]
    confidence: float
    description: str

class DocumentClassifier:
    """
    Service for classifying document types and suggesting appropriate schemas
    """
    
    def __init__(self):
        # Define document type patterns and keywords
        self.document_patterns = {
            DocumentType.INVOICE: {
                "keywords": [
                    "invoice", "bill", "statement", "amount due", "payment terms",
                    "invoice number", "invoice date", "due date", "total amount",
                    "subtotal", "tax", "balance due", "please pay"
                ],
                "regex_patterns": [
                    r"invoice\s+#?\d+",
                    r"bill\s+to:",
                    r"amount\s+due:?\s*\$",
                    r"payment\s+terms:",
                    r"due\s+date:"
                ],
                "schema": {
                    "name": "Invoice Schema",
                    "fields": [
                        {"name": "Invoice Number", "key": "invoice_number", "required": True},
                        {"name": "Invoice Date", "key": "invoice_date", "required": True},
                        {"name": "Due Date", "key": "due_date", "required": False},
                        {"name": "Vendor/Supplier", "key": "vendor", "required": True},
                        {"name": "Customer/Bill To", "key": "customer", "required": True},
                        {"name": "Subtotal", "key": "subtotal", "required": False},
                        {"name": "Tax Amount", "key": "tax_amount", "required": False},
                        {"name": "Total Amount", "key": "total_amount", "required": True},
                        {"name": "Payment Terms", "key": "payment_terms", "required": False},
                        {"name": "Description", "key": "description", "required": False}
                    ]
                }
            },
            
            DocumentType.RECEIPT: {
                "keywords": [
                    "receipt", "thank you", "payment received", "transaction",
                    "merchant", "store", "cashier", "register", "sale",
                    "purchase", "item", "quantity", "price"
                ],
                "regex_patterns": [
                    r"receipt\s+#?\d+",
                    r"thank\s+you\s+for\s+your\s+purchase",
                    r"merchant:\s+",
                    r"transaction\s+id:",
                    r"payment\s+received"
                ],
                "schema": {
                    "name": "Receipt Schema",
                    "fields": [
                        {"name": "Receipt Number", "key": "receipt_number", "required": True},
                        {"name": "Date", "key": "date", "required": True},
                        {"name": "Merchant/Store", "key": "merchant", "required": True},
                        {"name": "Transaction ID", "key": "transaction_id", "required": False},
                        {"name": "Items", "key": "items", "required": False},
                        {"name": "Subtotal", "key": "subtotal", "required": False},
                        {"name": "Tax", "key": "tax", "required": False},
                        {"name": "Total Amount", "key": "total_amount", "required": True},
                        {"name": "Payment Method", "key": "payment_method", "required": False}
                    ]
                }
            },
            
            DocumentType.BANK_STATEMENT: {
                "keywords": [
                    "bank statement", "account statement", "account number",
                    "balance", "deposits", "withdrawals", "transactions",
                    "opening balance", "closing balance", "bank name"
                ],
                "regex_patterns": [
                    r"bank\s+statement",
                    r"account\s+statement",
                    r"account\s+#?\d+",
                    r"opening\s+balance:?\s*\$",
                    r"closing\s+balance:?\s*\$",
                    r"statement\s+period:"
                ],
                "schema": {
                    "name": "Bank Statement Schema",
                    "fields": [
                        {"name": "Bank Name", "key": "bank_name", "required": True},
                        {"name": "Account Number", "key": "account_number", "required": True},
                        {"name": "Statement Period", "key": "statement_period", "required": True},
                        {"name": "Opening Balance", "key": "opening_balance", "required": True},
                        {"name": "Closing Balance", "key": "closing_balance", "required": True},
                        {"name": "Total Deposits", "key": "total_deposits", "required": False},
                        {"name": "Total Withdrawals", "key": "total_withdrawals", "required": False},
                        {"name": "Transactions", "key": "transactions", "required": False}
                    ]
                }
            },
            
            DocumentType.FINANCIAL_REPORT: {
                "keywords": [
                    "financial report", "annual report", "quarterly report",
                    "income statement", "balance sheet", "cash flow",
                    "revenue", "expenses", "profit", "loss", "assets",
                    "liabilities", "equity", "earnings", "ebitda"
                ],
                "regex_patterns": [
                    r"financial\s+report",
                    r"annual\s+report",
                    r"quarterly\s+report",
                    r"income\s+statement",
                    r"balance\s+sheet",
                    r"cash\s+flow\s+statement",
                    r"revenue:?\s*\$",
                    r"total\s+assets:?\s*\$"
                ],
                "schema": {
                    "name": "Financial Report Schema",
                    "fields": [
                        {"name": "Report Type", "key": "report_type", "required": True},
                        {"name": "Period", "key": "period", "required": True},
                        {"name": "Company Name", "key": "company_name", "required": True},
                        {"name": "Revenue", "key": "revenue", "required": False},
                        {"name": "Expenses", "key": "expenses", "required": False},
                        {"name": "Net Income", "key": "net_income", "required": False},
                        {"name": "Total Assets", "key": "total_assets", "required": False},
                        {"name": "Total Liabilities", "key": "total_liabilities", "required": False},
                        {"name": "Shareholders Equity", "key": "shareholders_equity", "required": False}
                    ]
                }
            },
            
            DocumentType.CONTRACT: {
                "keywords": [
                    "contract", "agreement", "terms and conditions",
                    "parties", "effective date", "expiration date",
                    "signature", "witness", "notary", "legal"
                ],
                "regex_patterns": [
                    r"contract\s+between",
                    r"agreement\s+dated",
                    r"effective\s+date:",
                    r"expiration\s+date:",
                    r"party\s+a:",
                    r"party\s+b:",
                    r"terms\s+and\s+conditions"
                ],
                "schema": {
                    "name": "Contract Schema",
                    "fields": [
                        {"name": "Contract Type", "key": "contract_type", "required": True},
                        {"name": "Parties", "key": "parties", "required": True},
                        {"name": "Effective Date", "key": "effective_date", "required": True},
                        {"name": "Expiration Date", "key": "expiration_date", "required": False},
                        {"name": "Contract Value", "key": "contract_value", "required": False},
                        {"name": "Terms", "key": "terms", "required": False},
                        {"name": "Signatures", "key": "signatures", "required": False}
                    ]
                }
            },
            
            DocumentType.TAX_DOCUMENT: {
                "keywords": [
                    "tax return", "w-2", "1099", "irs", "tax form",
                    "adjusted gross income", "taxable income", "refund",
                    "tax due", "social security", "federal tax"
                ],
                "regex_patterns": [
                    r"form\s+w-?2",
                    r"form\s+1099",
                    r"tax\s+return",
                    r"adjusted\s+gross\s+income",
                    r"taxable\s+income",
                    r"federal\s+tax\s+withheld"
                ],
                "schema": {
                    "name": "Tax Document Schema",
                    "fields": [
                        {"name": "Tax Form Type", "key": "tax_form_type", "required": True},
                        {"name": "Tax Year", "key": "tax_year", "required": True},
                        {"name": "Taxpayer Name", "key": "taxpayer_name", "required": True},
                        {"name": "Social Security Number", "key": "ssn", "required": False},
                        {"name": "Adjusted Gross Income", "key": "agi", "required": False},
                        {"name": "Taxable Income", "key": "taxable_income", "required": False},
                        {"name": "Federal Tax Withheld", "key": "federal_tax_withheld", "required": False},
                        {"name": "Refund Amount", "key": "refund_amount", "required": False},
                        {"name": "Tax Due", "key": "tax_due", "required": False}
                    ]
                }
            }
        }
    
    def classify_document(self, text: str) -> Tuple[DocumentType, float]:
        """
        Classify document type based on text content
        Returns (document_type, confidence_score)
        """
        text_lower = text.lower()
        
        # Calculate scores for each document type
        scores = {}
        
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            total_patterns = len(patterns["keywords"]) + len(patterns["regex_patterns"])
            
            # Check keyword matches
            for keyword in patterns["keywords"]:
                if keyword.lower() in text_lower:
                    score += 1
            
            # Check regex pattern matches
            for pattern in patterns["regex_patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 2  # Regex matches are weighted higher
            
            # Normalize score
            if total_patterns > 0:
                scores[doc_type] = score / total_patterns
            else:
                scores[doc_type] = 0
        
        # Find the document type with highest score
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] > 0.1:  # Minimum confidence threshold
                return best_type[0], best_type[1]
        
        return DocumentType.UNKNOWN, 0.0
    
    def get_schema_for_document_type(self, document_type: DocumentType) -> Optional[DocumentSchema]:
        """
        Get the appropriate schema for a document type
        """
        if document_type in self.document_patterns:
            schema_data = self.document_patterns[document_type]["schema"]
            return DocumentSchema(
                name=schema_data["name"],
                document_type=document_type,
                fields=schema_data["fields"],
                confidence=1.0,
                description=f"Schema for {document_type.value} documents"
            )
        return None
    
    def suggest_schema(self, text: str) -> DocumentSchema:
        """
        Analyze text and suggest the most appropriate schema
        """
        doc_type, confidence = self.classify_document(text)
        
        if doc_type == DocumentType.UNKNOWN:
            # Return a generic schema for unknown documents
            return DocumentSchema(
                name="Generic Document Schema",
                document_type=DocumentType.UNKNOWN,
                fields=[
                    {"name": "Document Type", "key": "document_type", "required": False},
                    {"name": "Date", "key": "date", "required": False},
                    {"name": "Amount", "key": "amount", "required": False},
                    {"name": "Parties", "key": "parties", "required": False},
                    {"name": "Description", "key": "description", "required": False},
                    {"name": "Reference Number", "key": "reference_number", "required": False}
                ],
                confidence=confidence,
                description="Generic schema for unidentified documents"
            )
        
        schema = self.get_schema_for_document_type(doc_type)
        if schema:
            schema.confidence = confidence
            return schema
        
        # Fallback to generic schema
        return DocumentSchema(
            name="Generic Document Schema",
            document_type=DocumentType.UNKNOWN,
            fields=[
                {"name": "Document Type", "key": "document_type", "required": False},
                {"name": "Date", "key": "date", "required": False},
                {"name": "Amount", "key": "amount", "required": False},
                {"name": "Parties", "key": "parties", "required": False},
                {"name": "Description", "key": "description", "required": False},
                {"name": "Reference Number", "key": "reference_number", "required": False}
            ],
            confidence=confidence,
            description="Generic schema for unidentified documents"
        )
    
    def map_entities_to_schema(self, entities: List[Any], schema: DocumentSchema) -> List[Dict[str, Any]]:
        """
        Map extracted entities to schema fields based on document type
        """
        mapped_results = []
        
        # Create field mapping based on document type
        field_mapping = self._get_field_mapping_for_type(schema.document_type)
        
        # Map entities to schema fields
        for entity in entities:
            mapped_field = self._find_best_field_match(entity, schema.fields, field_mapping)
            if mapped_field:
                mapped_results.append({
                    "field": mapped_field["name"],
                    "key": mapped_field["key"],
                    "value": entity.text,
                    "confidence": entity.confidence,
                    "entity_type": entity.type,
                    "schema_field": mapped_field["key"],
                    "required": mapped_field.get("required", False)
                })
        
        return mapped_results
    
    def _get_field_mapping_for_type(self, doc_type: DocumentType) -> Dict[str, List[str]]:
        """
        Get entity type to field mapping for specific document types
        """
        mappings = {
            DocumentType.INVOICE: {
                "PERSON": ["customer", "vendor"],
                "COMPANY": ["vendor", "customer"],
                "CURRENCY": ["total_amount", "subtotal", "tax_amount"],
                "DATE": ["invoice_date", "due_date"],
                "FINANCIAL_METRIC": ["total_amount", "subtotal"]
            },
            DocumentType.RECEIPT: {
                "PERSON": ["merchant"],
                "COMPANY": ["merchant"],
                "CURRENCY": ["total_amount", "subtotal", "tax"],
                "DATE": ["date"],
                "FINANCIAL_METRIC": ["total_amount"]
            },
            DocumentType.BANK_STATEMENT: {
                "COMPANY": ["bank_name"],
                "CURRENCY": ["opening_balance", "closing_balance", "total_deposits", "total_withdrawals"],
                "DATE": ["statement_period"],
                "FINANCIAL_METRIC": ["opening_balance", "closing_balance"]
            },
            DocumentType.FINANCIAL_REPORT: {
                "COMPANY": ["company_name"],
                "CURRENCY": ["revenue", "expenses", "net_income", "total_assets", "total_liabilities"],
                "DATE": ["period"],
                "FINANCIAL_METRIC": ["revenue", "expenses", "net_income", "total_assets"]
            }
        }
        
        return mappings.get(doc_type, {})
    
    def _find_best_field_match(self, entity: Any, schema_fields: List[Dict], field_mapping: Dict[str, List[str]]) -> Optional[Dict]:
        """
        Find the best matching schema field for an entity
        """
        # First try exact entity type mapping
        if entity.type in field_mapping:
            for field_key in field_mapping[entity.type]:
                for field in schema_fields:
                    if field["key"] == field_key:
                        return field
        
        # Then try keyword matching
        entity_text_lower = entity.text.lower()
        for field in schema_fields:
            field_name_lower = field["name"].lower()
            if any(word in entity_text_lower for word in field_name_lower.split()):
                return field
        
        # Finally, try partial matching
        for field in schema_fields:
            field_key_lower = field["key"].lower()
            if any(word in entity_text_lower for word in field_key_lower.split("_")):
                return field
        
        return None 