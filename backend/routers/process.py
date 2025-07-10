from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional, Tuple
import os
import json
from datetime import datetime, timedelta
import logging
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import numpy as np
from dataclasses import dataclass
import re
from collections import defaultdict
import uuid
import time
from backend.app.services.entity_recognition import FinancialEntityRecognizer, FinancialEntity
from backend.app.services.relationship_extraction import RelationshipExtractor, Relationship
from backend.app.services.celery_service import (
    process_document_task,
    update_entity_task,
    merge_entities_task,
    get_graph_metrics_task,
    analyze_entity_network_task,
    find_similar_entities_task,
    analyze_relationship_patterns_task,
    analyze_financial_metrics_task,
    analyze_company_relationships_task,
    analyze_market_trends_task,
    analyze_risk_factors_task
)
from backend.app.services.status_tracker import (
    StatusTracker,
    ProcessingStatus,
    ProcessingStage,
    ProcessingMetrics,
    DocumentStatus
)
from backend.app.models.graph_models import Entity, Relationship, EntityType, RelationshipType
from backend.app.services.neo4j_service import Neo4jService
from backend.app.services.validation_service import ValidationService, ValidationRule, EntityValidationRule, RelationshipValidationRule, ValidationResult, ValidationLevel
from backend.app.services.quality_control import QualityControlService, QualityMetricType
from backend.app.services.validation_pipeline import ValidationPipeline
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots
from fastapi.responses import JSONResponse
import networkx as nx
from backend.app.config import settings
from pydantic import BaseModel
from backend.app.models.validation_models import ValidationResult
from backend.app.models.correction_models import CorrectionStrategy
from backend.app.models.financial_domain import FinancialDomain

# Pydantic models for request/response
class ValidationRequest(BaseModel):
    rules: Optional[List[str]] = None

class ValidationResponse(BaseModel):
    document_id: str
    validation_results: List[ValidationResult]
    summary: Dict[str, Any]

class DocumentProcessRequest(BaseModel):
    extract_entities: bool = True
    extract_relationships: bool = True
    build_graph: bool = True

class DocumentProcessResponse(BaseModel):
    document_id: str
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    graph_data: Dict[str, Any]
    processing_time: float

class GraphDataRequest(BaseModel):
    document_id: str
    include_entities: bool = True
    include_relationships: bool = True
    max_nodes: Optional[int] = 100

class GraphDataResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class CorrectionRequest(BaseModel):
    document_id: str
    validation_result_id: str
    strategy: CorrectionStrategy
    description: str

class CorrectionResponse(BaseModel):
    correction_id: str
    document_id: str
    status: str
    applied_changes: Dict[str, Any]

# Optional docling utilities
try:
    from docling_parse.pdf_parser import DoclingPdfParser
    from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DoclingPdfParser = None
    HierarchicalChunker = None

router = APIRouter(
    tags=["Document Processing"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)
logger = logging.getLogger(__name__)
status_tracker = StatusTracker()
neo4j_service = Neo4jService(
    uri=settings.NEO4J_URI,
    user=settings.NEO4J_USER,
    password=settings.NEO4J_PASSWORD
)
validation_service = ValidationService()
quality_control = QualityControlService()
validation_pipeline = ValidationPipeline(validation_service, quality_control)

@dataclass
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]
    page: int
    font_size: float
    font_name: str
    is_bold: bool
    is_italic: bool
    alignment: str

@dataclass
class TableBlock:
    data: List[List[str]]
    bbox: Tuple[float, float, float, float]
    page: int
    confidence: float
    headers: List[str]
    rows: int
    columns: int

@dataclass
class ImageBlock:
    image: Image.Image
    bbox: Tuple[float, float, float, float]
    page: int
    type: str
    confidence: float
    description: Optional[str] = None

class DocumentProcessor:
    def __init__(self):
        if not DOCLING_AVAILABLE:
            logger.warning("Docling libraries not available. Some features will be limited.")
            self.parser = None
            self.chunker = None
        else:
            self.parser = DoclingPdfParser()
            self.chunker = HierarchicalChunker()
        
        # Initialize OCR if available
        try:
            pytesseract.get_tesseract_version()
            self.ocr_available = True
        except:
            self.ocr_available = False
            logger.warning("Tesseract OCR not available. Image text extraction will be limited.")
        
        self.entity_recognizer = FinancialEntityRecognizer()
        self.relationship_extractor = RelationshipExtractor()
    
    async def process_document(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process a document and extract entities and relationships
        """
        try:
            # Read file content
            content = await file.read()
            
            # Extract text from PDF
            text = self._extract_text(content)
            if not text:
                raise HTTPException(status_code=400, detail="Could not extract text from document")
            
            # Extract entities
            entities = self.entity_recognizer.extract_entities(text)
            
            # Extract relationships
            relationships = self.relationship_extractor.extract_relationships(
                text,
                entities,
                window_size=100
            )
            
            return {
                "entities": [self._entity_to_dict(e) for e in entities],
                "relationships": [self._relationship_to_dict(r) for r in relationships]
            }
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")
    
    def _extract_text(self, content: bytes) -> str:
        """Extract text from PDF content"""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ""
    
    def _entity_to_dict(self, entity: FinancialEntity) -> Dict[str, Any]:
        """Convert FinancialEntity to dictionary"""
        return {
            "id": entity.id,
            "text": entity.text,
            "type": entity.type,
            "confidence": entity.confidence,
            "metadata": entity.metadata
        }
    
    def _relationship_to_dict(self, relationship: Relationship) -> Dict[str, Any]:
        """Convert Relationship to dictionary"""
        return {
            "id": relationship.id,
            "source_id": relationship.source_id,
            "target_id": relationship.target_id,
            "type": relationship.type,
            "confidence": relationship.confidence,
            "metadata": relationship.metadata
        }

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return ""

@router.post("/documents/{document_id}/process", response_model=DocumentProcessResponse)
async def process_document(document_id: str, request: DocumentProcessRequest):
    """Process a document and extract entities and relationships"""
    try:
        start_time = time.time()
        
        # Get document file path
        data_dir = os.path.join(os.getcwd(), "..", "data")
        document_dir = os.path.join(data_dir, document_id)
        
        if not os.path.exists(document_dir):
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
        # Find PDF file in document directory
        pdf_files = [f for f in os.listdir(document_dir) if f.endswith('.pdf')]
        if not pdf_files:
            raise HTTPException(status_code=404, detail=f"No PDF file found for document {document_id}")
        
        pdf_path = os.path.join(document_dir, pdf_files[0])
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from document")
        
        # Initialize services
        entity_recognizer = FinancialEntityRecognizer()
        relationship_extractor = RelationshipExtractor()
        
        # Extract entities
        entities = entity_recognizer.extract_entities(text)
        
        # Extract relationships
        relationships = relationship_extractor.extract_relationships(
            text,
            entities,
            window_size=100
        )
        
        # Store in Neo4j
        stored_entities = []
        stored_relationships = []
        
        for entity in entities:
            try:
                # Set source document
                entity.source_document = document_id
                entity_id = neo4j_service.create_entity(entity)
                stored_entities.append(entity)
            except Exception as e:
                logger.error(f"Failed to store entity {entity.text}: {str(e)}")
        
        for relationship in relationships:
            try:
                # Set source document
                relationship.source_document = document_id
                relationship_id = neo4j_service.create_relationship(relationship)
                stored_relationships.append(relationship)
            except Exception as e:
                logger.error(f"Failed to store relationship {relationship.id}: {str(e)}")
        
        # Prepare graph data
        graph_data = {
            "total_entities": len(stored_entities),
            "total_relationships": len(stored_relationships),
            "document_id": document_id
        }
        
        processing_time = time.time() - start_time
        
        # Helper to coerce entity/relationship type to enum value
        def coerce_entity_type(entity_type):
            # Map common snake_case/uppercase types to enum values
            mapping = {
                'CURRENCY': 'Currency',
                'currency': 'Currency',
                'ORGANIZATION': 'Company',
                'organization': 'Company',
                'COMPANY': 'Company',
                'company': 'Company',
                'PERSON': 'Person',
                'person': 'Person',
                'DATE': 'Date',
                'date': 'Date',
                'AMOUNT': 'FinancialMetric',
                'amount': 'FinancialMetric',
                'ACCOUNT': 'Account',
                'account': 'Account',
                'LOCATION': 'Location',
                'location': 'Location',
                'METRIC': 'FinancialMetric',
                'metric': 'FinancialMetric',
                'FINANCIAL_METRIC': 'FinancialMetric',
                'Financial_metric': 'FinancialMetric',
                'financial_metric': 'FinancialMetric',
                'INSTRUMENT': 'FinancialInstrument',
                'instrument': 'FinancialInstrument',
                'FINANCIAL_INSTRUMENT': 'FinancialInstrument',
                'financial_instrument': 'FinancialInstrument',
                'EVENT': 'Event',
                'event': 'Event',
                'TRANSACTION': 'Transaction',
                'transaction': 'Transaction',
                'MARKET': 'Market',
                'market': 'Market',
                'INDUSTRY': 'Industry',
                'industry': 'Industry',
                'DOCUMENT': 'Document',
                'document': 'Document',
                'REGULATION': 'Regulation',
                'regulation': 'Regulation',
                'INTELLECTUAL_PROPERTY': 'IntellectualProperty',
                'intellectual_property': 'IntellectualProperty',
                'PORTFOLIO': 'Portfolio',
                'portfolio': 'Portfolio',
                'POLICY': 'Policy',
                'policy': 'Policy',
                'PROPERTY': 'Property',
                'property': 'Property',
                'CRYPTO_ASSET': 'CryptoAsset',
                'crypto_asset': 'CryptoAsset',
                'FINTECH_SERVICE': 'FintechService',
                'fintech_service': 'FintechService',
                'REGULATORY_REPORT': 'RegulatoryReport',
                'regulatory_report': 'RegulatoryReport',
                'COMPLIANCE_CHECK': 'ComplianceCheck',
                'compliance_check': 'ComplianceCheck',
                'FUND': 'Fund',
                'fund': 'Fund',
                'SYSTEM': 'System',
                'system': 'System',
                'UNKNOWN': 'Unknown',
                'unknown': 'Unknown',
            }
            if not entity_type:
                return 'Unknown'
            if entity_type in mapping:
                return mapping[entity_type]
            # Try to convert snake_case to CamelCase
            if '_' in entity_type:
                return ''.join([w.capitalize() for w in entity_type.split('_')])
            # Capitalize if not mapped
            return entity_type.capitalize()

        def coerce_relationship_type(rel_type):
            # Only allow valid enum values
            valid_types = {
                'OWNS', 'HAS_SUBSIDIARY', 'HAS_JOINT_VENTURE', 'WORKS_FOR', 'REPORTS_TO', 'IS_BOARD_MEMBER', 'EMPLOYMENT',
                'HAS_METRIC', 'HAS_REVENUE', 'HAS_PROFIT', 'HAS_ASSET', 'HAS_LIABILITY', 'HAS_INVESTMENT', 'HAS_DEBT', 'HAS_EQUITY',
                'ISSUES', 'ACQUIRES', 'MERGES_WITH', 'JOINT_VENTURE', 'STRATEGIC_ALLIANCE', 'COMPETES_WITH', 'SUPPLIES_TO', 'CUSTOMER_OF',
                'OPERATES_IN', 'HEADQUARTERED_IN', 'HAS_OFFICE_IN', 'FOUNDED_ON', 'ACQUIRED_ON', 'MERGED_ON', 'LOCATED_IN',
                'HAS_WAREHOUSE_IN', 'HAS_RETAIL_IN', 'HAS_DISTRIBUTION_IN', 'HAS_CURRENT_RATIO', 'HAS_QUICK_RATIO', 'HAS_DEBT_TO_EQUITY',
                'HAS_INTEREST_COVERAGE', 'HAS_ASSET_TURNOVER', 'HAS_INVENTORY_TURNOVER', 'HAS_RECEIVABLES_TURNOVER', 'HAS_PAYABLES_TURNOVER',
                'HAS_WORKING_CAPITAL', 'HAS_FREE_CASH_FLOW', 'HAS_OPERATING_CASH_FLOW', 'HAS_INVESTING_CASH_FLOW', 'HAS_FINANCING_CASH_FLOW',
                'HAS_CAPITAL_EXPENDITURE', 'HAS_DEPRECIATION', 'HAS_AMORTIZATION', 'HAS_GOODWILL', 'HAS_INTANGIBLE_ASSETS', 'HAS_TANGIBLE_ASSETS',
                'HAS_FIXED_ASSETS', 'HAS_CURRENT_ASSETS', 'HAS_NON_CURRENT_ASSETS', 'HAS_CURRENT_LIABILITIES', 'HAS_NON_CURRENT_LIABILITIES',
                'HAS_LONG_TERM_DEBT', 'HAS_SHORT_TERM_DEBT', 'HAS_ACCOUNTS_RECEIVABLE', 'HAS_ACCOUNTS_PAYABLE', 'HAS_INVENTORY',
                'HAS_PREPAID_EXPENSES', 'HAS_DEFERRED_REVENUE', 'HAS_ACCUMULATED_DEPRECIATION', 'HAS_RETAINED_EARNINGS', 'HAS_TREASURY_STOCK',
                'HAS_PREFERRED_STOCK', 'HAS_COMMON_STOCK', 'HAS_ADDITIONAL_PAID_IN_CAPITAL', 'HAS_OTHER_COMPREHENSIVE_INCOME',
                'HAS_MINORITY_INTEREST', 'HAS_OPERATING_INCOME', 'HAS_NON_OPERATING_INCOME', 'HAS_EXTRAORDINARY_ITEMS', 'HAS_DISCONTINUED_OPERATIONS',
                'HAS_TAX_EXPENSE', 'HAS_INTEREST_EXPENSE', 'HAS_DIVIDEND_PAYOUT', 'HAS_DIVIDEND_YIELD', 'HAS_EARNINGS_YIELD', 'HAS_BOOK_VALUE',
                'HAS_TANGIBLE_BOOK_VALUE', 'HAS_PRICE_TO_BOOK', 'HAS_PRICE_TO_SALES', 'HAS_PRICE_TO_CASH_FLOW', 'HAS_ENTERPRISE_VALUE',
                'HAS_EV_TO_SALES', 'HAS_EV_TO_EBITDA', 'HAS_EV_TO_EBIT', 'HAS_NET_DEBT', 'HAS_NET_DEBT_TO_EBITDA', 'HAS_CAPITAL_STRUCTURE',
                'HAS_WEIGHTED_AVERAGE_COST_OF_CAPITAL', 'HAS_BETA', 'HAS_ALPHA', 'HAS_SHARPE_RATIO', 'HAS_SORTINO_RATIO', 'HAS_INFORMATION_RATIO',
                'HAS_TREYNOR_RATIO', 'HAS_JENSENS_ALPHA', 'HAS_CAPM', 'HAS_DIVIDEND_DISCOUNT_MODEL', 'HAS_DCF', 'HAS_RESIDUAL_INCOME', 'HAS_EVA',
                'HAS_MVA', 'HAS_TOTAL_SHAREHOLDER_RETURN', 'HAS_INTERNAL_RATE_OF_RETURN', 'HAS_NET_PRESENT_VALUE', 'HAS_PAYBACK_PERIOD',
                'HAS_PROFITABILITY_INDEX', 'HAS_MODIFIED_INTERNAL_RATE_OF_RETURN', 'TRANSACTION', 'BELONGS_TO'
            }
            # Accept as-is if valid
            if rel_type in valid_types:
                return rel_type
            # Try uppercase
            if rel_type and rel_type.upper() in valid_types:
                return rel_type.upper()
            # Fallback
            return 'TRANSACTION'

        def to_entity_dict(e):
            # Convert to dict and coerce fields
            if hasattr(e, 'model_dump'):
                d = e.model_dump()
            elif hasattr(e, 'dict'):
                d = e.dict()
            elif hasattr(e, '__dict__'):
                d = dict(e.__dict__)
            else:
                from dataclasses import asdict
                d = asdict(e)
            # Ensure required fields
            d['id'] = d.get('id') or str(uuid.uuid4())
            d['name'] = d.get('name') or d.get('text') or 'Unknown'
            d['type'] = coerce_entity_type(d.get('type'))
            # Ensure metadata is serializable
            if 'metadata' in d and d['metadata']:
                # Convert complex objects to strings
                for key, value in d['metadata'].items():
                    if not isinstance(value, (str, int, float, bool, list, dict)):
                        d['metadata'][key] = str(value)
            return d

        def to_relationship_dict(r):
            if hasattr(r, 'model_dump'):
                d = r.model_dump()
            elif hasattr(r, 'dict'):
                d = r.dict()
            elif hasattr(r, '__dict__'):
                d = dict(r.__dict__)
            else:
                from dataclasses import asdict
                d = asdict(r)
            d['id'] = d.get('id') or str(uuid.uuid4())
            d['type'] = coerce_relationship_type(d.get('type'))
            # Ensure metadata is serializable
            if 'metadata' in d and d['metadata']:
                # Convert complex objects to strings
                for key, value in d['metadata'].items():
                    if not isinstance(value, (str, int, float, bool, list, dict)):
                        d['metadata'][key] = str(value)
            return d

        # Filter and fix entities/relationships
        entity_dicts = [to_entity_dict(e) for e in stored_entities if e]
        relationship_dicts = [to_relationship_dict(r) for r in stored_relationships if r]

        result = DocumentProcessResponse(
            document_id=document_id,
            entities=entity_dicts,
            relationships=relationship_dicts,
            graph_data=graph_data,
            processing_time=processing_time
        )
        
        logger.info(f"Document processing completed in {processing_time:.2f} seconds")
        return result
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

# Graph visualization endpoints
@router.get("/graph/{document_id}", response_model=GraphDataResponse)
async def get_graph_data(document_id: str, request: GraphDataRequest = Depends()):
    """Get graph data for visualization"""
    try:
        # Get graph data from Neo4j
        graph_data = neo4j_service.get_graph_data(document_id, request.max_nodes)
        
        # Convert to visualization format
        nodes = []
        edges = []
        
        # Add entities as nodes
        for entity in graph_data.get("entities", []):
            nodes.append({
                "id": entity.get("id", str(uuid.uuid4())),
                "label": entity.get("properties", {}).get("name", entity.get("text", "Unknown")),
                "type": entity.get("type", "UNKNOWN"),
                "properties": entity.get("properties", {}),
                "confidence": entity.get("confidence", 0.0)
            })
        
        # Add relationships as edges
        for rel in graph_data.get("relationships", []):
            edges.append({
                "id": rel.get("id", str(uuid.uuid4())),
                "source": rel.get("source_id"),
                "target": rel.get("target_id"),
                "type": rel.get("type", "UNKNOWN"),
                "properties": rel.get("properties", {}),
                "confidence": rel.get("confidence", 0.0)
            })
        
        metadata = {
            "document_id": document_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return GraphDataResponse(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error getting graph data for {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {str(e)}")

@router.get("/documents/{document_id}/status", response_model=Dict[str, Any])
async def get_document_status(document_id: str) -> Dict[str, Any]:
    """
    Get the processing status of a document.
    
    Args:
        document_id: Unique identifier for the document
        
    Returns:
        Dict containing current processing status
        
    Raises:
        HTTPException: If document not found
    """
    try:
        status = status_tracker.get_status(document_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document status: {str(e)}"
        )

@router.get("/documents/status", response_model=Dict[str, Any])
async def get_all_statuses() -> Dict[str, Any]:
    """
    Get the processing status of all documents.
    
    Returns:
        Dict containing status of all documents
    """
    try:
        return status_tracker.get_all_statuses()
    except Exception as e:
        logger.error(f"Error getting all statuses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statuses: {str(e)}"
        )

@router.get("/metrics", response_model=Dict[str, Any])
async def get_processing_metrics() -> Dict[str, Any]:
    """
    Get current processing metrics.
    
    Returns:
        Dict containing processing metrics
    """
    try:
        return status_tracker.get_metrics()
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )

@router.post("/entities/{entity_id}/update", response_model=Dict[str, Any])
async def update_entity(
    entity_id: str,
    properties: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Update properties of an entity.
    
    Args:
        entity_id: Unique identifier for the entity
        properties: New properties to update
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict containing task ID and status
    """
    try:
        task = update_entity_task.delay(entity_id, properties)
        return {
            "status": "success",
            "task_id": task.id,
            "entity_id": entity_id,
            "message": "Entity update started"
        }
    except Exception as e:
        logger.error(f"Error updating entity: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update entity: {str(e)}"
        )

@router.post("/entities/merge", response_model=Dict[str, Any])
async def merge_entities(
    source_id: str,
    target_id: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Merge two entities.
    
    Args:
        source_id: ID of the source entity
        target_id: ID of the target entity
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict containing task ID and status
    """
    try:
        task = merge_entities_task.delay(source_id, target_id)
        return {
            "status": "success",
            "task_id": task.id,
            "source_id": source_id,
            "target_id": target_id,
            "message": "Entity merge started"
        }
    except Exception as e:
        logger.error(f"Error merging entities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to merge entities: {str(e)}"
        )

@router.get("/graph/metrics", response_model=Dict[str, Any])
async def get_graph_metrics(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Get graph metrics.
    
    Args:
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict containing task ID and status
    """
    try:
        task = get_graph_metrics_task.delay()
        return {
            "status": "success",
            "task_id": task.id,
            "message": "Graph metrics calculation started"
        }
    except Exception as e:
        logger.error(f"Error getting graph metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph metrics: {str(e)}"
        )

# New visualization endpoints
@router.get("/visualize/entity-network/{entity_id}", response_model=Dict[str, Any])
async def visualize_entity_network(
    entity_id: str,
    depth: int = 2,
    relationship_types: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Visualize the network of relationships around an entity.
    
    Args:
        entity_id: ID of the central entity
        depth: Maximum depth of relationships to include
        relationship_types: Optional list of relationship types to include
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict containing network visualization data
    """
    try:
        task = analyze_entity_network_task.delay(
            entity_id,
            depth,
            relationship_types
        )
        return {
            "status": "success",
            "task_id": task.id,
            "entity_id": entity_id,
            "message": "Network analysis started"
        }
    except Exception as e:
        logger.error(f"Error visualizing entity network: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to visualize network: {str(e)}"
        )

@router.get("/visualize/financial-metrics/{entity_id}", response_model=Dict[str, Any])
async def visualize_financial_metrics(
    entity_id: str,
    time_period: str = "1y",
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Visualize financial metrics for an entity over time.
    
    Args:
        entity_id: ID of the entity
        time_period: Time period for analysis (e.g., "1y", "6m", "3m")
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict containing financial metrics visualization data
    """
    try:
        task = analyze_financial_metrics_task.delay(
            entity_id,
            time_period
        )
        return {
            "status": "success",
            "task_id": task.id,
            "entity_id": entity_id,
            "message": "Financial metrics analysis started"
        }
    except Exception as e:
        logger.error(f"Error visualizing financial metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to visualize metrics: {str(e)}"
        )

@router.get("/visualize/market-trends/{industry}", response_model=Dict[str, Any])
async def visualize_market_trends(
    industry: str,
    time_period: str = "1y",
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Visualize market trends for a specific industry.
    
    Args:
        industry: Industry name to analyze
        time_period: Time period for analysis
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict containing market trends visualization data
    """
    try:
        task = analyze_market_trends_task.delay(
            industry,
            time_period
        )
        return {
            "status": "success",
            "task_id": task.id,
            "industry": industry,
            "message": "Market trends analysis started"
        }
    except Exception as e:
        logger.error(f"Error visualizing market trends: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to visualize trends: {str(e)}"
        )

@router.get("/visualize/risk-factors/{entity_id}", response_model=Dict[str, Any])
async def visualize_risk_factors(
    entity_id: str,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Visualize risk factors for an entity.
    
    Args:
        entity_id: ID of the entity
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict containing risk factors visualization data
    """
    try:
        task = analyze_risk_factors_task.delay(entity_id)
        return {
            "status": "success",
            "task_id": task.id,
            "entity_id": entity_id,
            "message": "Risk factors analysis started"
        }
    except Exception as e:
        logger.error(f"Error visualizing risk factors: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to visualize risk factors: {str(e)}"
        )

@router.get("/visualize/company-relationships/{company_id}", response_model=Dict[str, Any])
async def visualize_company_relationships(
    company_id: str,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Visualize relationships between a company and other entities.
    
    Args:
        company_id: ID of the company
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict containing company relationships visualization data
    """
    try:
        task = analyze_company_relationships_task.delay(company_id)
        return {
            "status": "success",
            "task_id": task.id,
            "company_id": company_id,
            "message": "Company relationships analysis started"
        }
    except Exception as e:
        logger.error(f"Error visualizing company relationships: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to visualize relationships: {str(e)}"
        )

@router.get("/performance")
async def get_performance_report(
    start_time: Optional[datetime] = Query(None, description="Start time for the report period"),
    end_time: Optional[datetime] = Query(None, description="End time for the report period")
) -> Dict[str, Any]:
    """Get a performance report for the specified time period"""
    try:
        return status_tracker.get_performance_report(start_time, end_time)
        
    except Exception as e:
        logger.error(f"Error getting performance report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting performance report: {str(e)}"
        )

@router.get("/history/{document_id}")
async def get_document_history(
    document_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time for the history"),
    end_time: Optional[datetime] = Query(None, description="End time for the history")
) -> List[Dict[str, Any]]:
    """Get processing history for a document"""
    try:
        return status_tracker.get_processing_history(document_id, start_time, end_time)
        
    except Exception as e:
        logger.error(f"Error getting document history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document history: {str(e)}"
        )

@router.get("/entities/{entity_id}/similar")
async def find_similar_entities(
    entity_id: str,
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
) -> Dict[str, Any]:
    """Find similar entities based on properties and relationships"""
    try:
        task = find_similar_entities_task.delay(
            entity_id=entity_id,
            similarity_threshold=similarity_threshold,
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password"
        )
        
        return {
            "status": "processing",
            "entity_id": entity_id,
            "task_id": task.id,
            "message": "Similarity search started"
        }
        
    except Exception as e:
        logger.error(f"Error finding similar entities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error finding similar entities: {str(e)}"
        )

@router.get("/relationships/patterns")
async def analyze_relationship_patterns(
    entity_type: str,
    relationship_type: str
) -> Dict[str, Any]:
    """Analyze patterns in relationships of a specific type"""
    try:
        task = analyze_relationship_patterns_task.delay(
            entity_type=entity_type,
            relationship_type=relationship_type,
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password"
        )
        
        return {
            "status": "processing",
            "entity_type": entity_type,
            "relationship_type": relationship_type,
            "task_id": task.id,
            "message": "Pattern analysis started"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing relationship patterns: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing relationship patterns: {str(e)}"
        )

# New validation endpoints
@router.post("/validate/entity", response_model=Dict[str, Any])
async def validate_entity(
    entity: Entity,
    update_quality: bool = True
) -> Dict[str, Any]:
    """
    Validate an entity against validation rules and update quality metrics.
    
    Args:
        entity: Entity to validate
        update_quality: Whether to update quality metrics
        
    Returns:
        Dict containing validation report and quality metrics
    """
    try:
        validation_report, quality_metrics = validation_pipeline.validate_entity_pipeline(
            entity,
            update_quality
        )
        
        return {
            "status": "success",
            "entity_id": entity.id,
            "validation_report": validation_report.dict(),
            "quality_metrics": quality_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error validating entity: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate entity: {str(e)}"
        )

@router.post("/validate/relationship", response_model=Dict[str, Any])
async def validate_relationship(
    relationship: Relationship,
    source_entity_id: Optional[str] = None,
    target_entity_id: Optional[str] = None,
    update_quality: bool = True
) -> Dict[str, Any]:
    """
    Validate a relationship against validation rules and update quality metrics.
    
    Args:
        relationship: Relationship to validate
        source_entity_id: Optional ID of source entity
        target_entity_id: Optional ID of target entity
        update_quality: Whether to update quality metrics
        
    Returns:
        Dict containing validation report and quality metrics
    """
    try:
        # Get source and target entities if IDs provided
        source_entity = None
        target_entity = None
        
        if source_entity_id:
            source_entity = neo4j_service.get_entity(source_entity_id)
        if target_entity_id:
            target_entity = neo4j_service.get_entity(target_entity_id)
            
        validation_report, quality_metrics = validation_pipeline.validate_relationship_pipeline(
            relationship,
            source_entity,
            target_entity,
            update_quality
        )
        
        return {
            "status": "success",
            "relationship_id": relationship.id,
            "validation_report": validation_report.dict(),
            "quality_metrics": quality_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error validating relationship: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate relationship: {str(e)}"
        )

@router.get("/validate/rules", response_model=Dict[str, Any])
async def get_validation_rules() -> Dict[str, Any]:
    """
    Get all validation rules.
    
    Returns:
        Dict containing validation rules
    """
    try:
        rules = validation_service.get_validation_rules()
        return {
            "status": "success",
            "rules": rules,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting validation rules: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation rules: {str(e)}"
        )

@router.post("/validate/rules", response_model=Dict[str, Any])
async def update_validation_rule(rule: ValidationRule) -> Dict[str, Any]:
    """
    Update or add a validation rule.
    
    Args:
        rule: Validation rule to update or add
        
    Returns:
        Dict containing update status
    """
    try:
        success = validation_service.update_validation_rule(rule)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update validation rule"
            )
            
        return {
            "status": "success",
            "message": "Validation rule updated successfully",
            "rule": rule.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating validation rule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update validation rule: {str(e)}"
        )

@router.get("/validate/quality", response_model=Dict[str, Any])
async def get_quality_metrics(
    entity_type: Optional[EntityType] = None
) -> Dict[str, Any]:
    """
    Get quality metrics for entities or overall.
    
    Args:
        entity_type: Optional entity type to filter metrics
        
    Returns:
        Dict containing quality metrics
    """
    try:
        report = quality_control.get_quality_report(entity_type)
        return {
            "status": "success",
            "metrics": report,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting quality metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quality metrics: {str(e)}"
        )

@router.get("/validate/summary", response_model=Dict[str, Any])
async def get_validation_summary(
    entity_type: Optional[EntityType] = None
) -> Dict[str, Any]:
    """
    Get a summary of validation and quality metrics.
    
    Args:
        entity_type: Optional entity type to filter summary
        
    Returns:
        Dict containing validation summary
    """
    try:
        summary = validation_pipeline.get_validation_summary(entity_type)
        return {
            "status": "success",
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting validation summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation summary: {str(e)}"
        )

@router.get("/visualize/quality/trends")
async def visualize_quality_trends(
    metric_type: Optional[QualityMetricType] = None,
    entity_type: Optional[EntityType] = None,
    days: int = 30,
    group_by: str = "day"
):
    """Generate time series plot of quality metric trends"""
    try:
        trend_data = quality_control.get_historical_metrics(
            metric_type=metric_type,
            entity_type=entity_type,
            days=days
        )
        
        if not trend_data:
            raise HTTPException(status_code=404, detail="No trend data available")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(trend_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Group data based on specified interval
        if group_by == "hour":
            df['group'] = df['timestamp'].dt.floor('H')
        elif group_by == "day":
            df['group'] = df['timestamp'].dt.date
        elif group_by == "week":
            df['group'] = df['timestamp'].dt.isocalendar().week
        elif group_by == "month":
            df['group'] = df['timestamp'].dt.to_period('M')
        
        # Calculate statistics for each group
        grouped_data = df.groupby(['group', 'metric_type']).agg({
            'value': ['mean', 'min', 'max', 'std'],
            'confidence_score': 'mean'
        }).reset_index()
        
        # Create interactive time series plot
        fig = go.Figure()
        
        for metric_type in grouped_data['metric_type'].unique():
            metric_data = grouped_data[grouped_data['metric_type'] == metric_type]
            
            # Add main line
            fig.add_trace(go.Scatter(
                x=metric_data['group'],
                y=metric_data[('value', 'mean')],
                name=f"{metric_type} (Mean)",
                line=dict(width=2),
                mode='lines+markers'
            ))
            
            # Add confidence interval
            fig.add_trace(go.Scatter(
                x=metric_data['group'],
                y=metric_data[('value', 'mean')] + metric_data[('value', 'std')],
                fill=None,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                name=f"{metric_type} Upper Bound"
            ))
            
            fig.add_trace(go.Scatter(
                x=metric_data['group'],
                y=metric_data[('value', 'mean')] - metric_data[('value', 'std')],
                fill='tonexty',
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                name=f"{metric_type} Lower Bound"
            ))
        
        # Update layout
        fig.update_layout(
            title="Quality Metrics Trends",
            xaxis_title="Time",
            yaxis_title="Metric Value",
            hovermode="x unified",
            showlegend=True,
            template="plotly_white"
        )
        
        return {"plot": fig.to_json()}
        
    except Exception as e:
        logger.error(f"Error generating quality trends visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/benchmarks")
async def visualize_quality_benchmarks(
    entity_type: EntityType,
    metric_types: Optional[List[QualityMetricType]] = None
):
    """Generate radar chart comparing current, average, and threshold values"""
    try:
        # Get benchmark data
        benchmark_data = quality_control.get_benchmarks(
            entity_type=entity_type,
            metric_types=metric_types
        )
        
        if not benchmark_data:
            raise HTTPException(status_code=404, detail="No benchmark data available")
        
        # Create radar chart
        fig = go.Figure()
        
        # Add current values
        fig.add_trace(go.Scatterpolar(
            r=[b['current_value'] for b in benchmark_data],
            theta=[b['metric_type'] for b in benchmark_data],
            fill='toself',
            name='Current'
        ))
        
        # Add average values
        fig.add_trace(go.Scatterpolar(
            r=[b['average_value'] for b in benchmark_data],
            theta=[b['metric_type'] for b in benchmark_data],
            fill='toself',
            name='Average'
        ))
        
        # Add threshold values
        fig.add_trace(go.Scatterpolar(
            r=[b['threshold'] for b in benchmark_data],
            theta=[b['metric_type'] for b in benchmark_data],
            fill='toself',
            name='Threshold'
        ))
        
        # Update layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title=f"Quality Benchmarks for {entity_type}",
            template="plotly_white"
        )
        
        return {"plot": fig.to_json()}
        
    except Exception as e:
        logger.error(f"Error generating quality benchmarks visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/impact")
async def visualize_quality_impact(
    entity_type: EntityType,
    metric_types: Optional[List[QualityMetricType]] = None
):
    """Generate bar chart for quality impact analysis"""
    try:
        # Get impact analysis data
        impact_data = quality_control.get_impact_analysis(
            entity_type=entity_type,
            metric_types=metric_types
        )
        
        if not impact_data:
            raise HTTPException(status_code=404, detail="No impact analysis data available")
        
        # Create bar chart
        fig = go.Figure()
        
        # Add impact scores
        fig.add_trace(go.Bar(
            x=[d['metric_type'] for d in impact_data],
            y=[d['impact_score'] for d in impact_data],
            name='Impact Score',
            marker_color='rgb(55, 83, 109)'
        ))
        
        # Add current values
        fig.add_trace(go.Bar(
            x=[d['metric_type'] for d in impact_data],
            y=[d['current_value'] for d in impact_data],
            name='Current Value',
            marker_color='rgb(26, 118, 255)'
        ))
        
        # Add threshold values
        fig.add_trace(go.Bar(
            x=[d['metric_type'] for d in impact_data],
            y=[d['threshold'] for d in impact_data],
            name='Threshold',
            marker_color='rgb(255, 65, 54)'
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Quality Impact Analysis for {entity_type}",
            xaxis_title="Metric Type",
            yaxis_title="Value",
            barmode='group',
            showlegend=True,
            template="plotly_white"
        )
        
        return {"plot": fig.to_json()}
        
    except Exception as e:
        logger.error(f"Error generating quality impact visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/validation/results")
async def visualize_validation_results(
    entity_type: Optional[EntityType] = None,
    days: int = 30
):
    """Generate pie charts for validation results distribution"""
    try:
        # Get validation results
        validation_results = validation_service.get_validation_results(
            entity_type=entity_type,
            days=days
        )
        
        if not validation_results:
            raise HTTPException(status_code=404, detail="No validation results found")
        
        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "pie"}]],
            subplot_titles=("Validation Results by Level", "Validation Results by Rule")
        )
        
        # Add validation level distribution
        level_counts = pd.Series([r['level'] for r in validation_results]).value_counts()
        fig.add_trace(
            go.Pie(
                labels=level_counts.index,
                values=level_counts.values,
                name="By Level"
            ),
            row=1, col=1
        )
        
        # Add rule distribution
        rule_counts = pd.Series([r['rule_name'] for r in validation_results]).value_counts()
        fig.add_trace(
            go.Pie(
                labels=rule_counts.index,
                values=rule_counts.values,
                name="By Rule"
            ),
            row=1, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Validation Results Distribution",
            showlegend=True,
            template="plotly_white"
        )
        
        return {"plot": fig.to_json()}
        
    except Exception as e:
        logger.error(f"Error generating validation results visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/validation/corrections")
async def visualize_validation_corrections(
    entity_type: Optional[EntityType] = None,
    days: int = 30
):
    """Generate bar chart for suggested corrections"""
    try:
        # Get validation results with corrections
        validation_results = validation_service.get_validation_results(
            entity_type=entity_type,
            days=days
        )
        
        if not validation_results:
            raise HTTPException(status_code=404, detail="No validation results found")
        
        # Extract corrections
        corrections = []
        for result in validation_results:
            if 'suggested_corrections' in result:
                for correction in result['suggested_corrections']:
                    corrections.append({
                        'rule': result['rule_name'],
                        'action': correction['action'],
                        'field': correction['field']
                    })
        
        if not corrections:
            raise HTTPException(status_code=404, detail="No corrections found")
        
        # Create DataFrame
        df = pd.DataFrame(corrections)
        
        # Group by rule and action
        grouped = df.groupby(['rule', 'action']).size().reset_index(name='count')
        
        # Create bar chart
        fig = go.Figure()
        
        for action in grouped['action'].unique():
            action_data = grouped[grouped['action'] == action]
            fig.add_trace(go.Bar(
                x=action_data['rule'],
                y=action_data['count'],
                name=action
            ))
        
        # Update layout
        fig.update_layout(
            title="Suggested Corrections by Rule and Action",
            xaxis_title="Rule",
            yaxis_title="Count",
            barmode='group',
            showlegend=True,
            template="plotly_white"
        )
        
        return {"plot": fig.to_json()}
        
    except Exception as e:
        logger.error(f"Error generating validation corrections visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/anomalies")
async def visualize_quality_anomalies(
    metric_type: QualityMetricType,
    entity_type: Optional[EntityType] = None,
    days: int = 30
):
    """Generate visualization of quality metric anomalies"""
    try:
        # Get historical metrics
        metrics = quality_control.get_historical_metrics(
            metric_type=metric_type,
            entity_type=entity_type,
            days=days
        )
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metric data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(metrics)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Detect anomalies using Z-score
        df['z_score'] = np.abs((df['value'] - df['value'].mean()) / df['value'].std())
        df['is_anomaly'] = df['z_score'] > 2  # Threshold of 2 standard deviations
        
        # Create scatter plot
        fig = go.Figure()
        
        # Add normal points
        normal_data = df[~df['is_anomaly']]
        fig.add_trace(go.Scatter(
            x=normal_data['timestamp'],
            y=normal_data['value'],
            mode='markers',
            name='Normal',
            marker=dict(color='blue')
        ))
        
        # Add anomaly points
        anomaly_data = df[df['is_anomaly']]
        fig.add_trace(go.Scatter(
            x=anomaly_data['timestamp'],
            y=anomaly_data['value'],
            mode='markers',
            name='Anomaly',
            marker=dict(color='red', size=10)
        ))
        
        # Add mean line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=[df['value'].mean()] * len(df),
            mode='lines',
            name='Mean',
            line=dict(color='green', dash='dash')
        ))
        
        # Add standard deviation bands
        std = df['value'].std()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=[df['value'].mean() + 2*std] * len(df),
            mode='lines',
            name='Upper Bound',
            line=dict(color='gray', dash='dot')
        ))
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=[df['value'].mean() - 2*std] * len(df),
            mode='lines',
            name='Lower Bound',
            line=dict(color='gray', dash='dot')
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Quality Metric Anomalies: {metric_type}",
            xaxis_title="Time",
            yaxis_title="Value",
            showlegend=True,
            template="plotly_white"
        )
        
        return {"plot": fig.to_json()}
        
    except Exception as e:
        logger.error(f"Error generating quality anomalies visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/correlation")
async def visualize_quality_correlation(
    entity_type: EntityType,
    metric_types: List[QualityMetricType]
):
    """Generate correlation matrix heatmap for quality metrics"""
    try:
        # Get metrics data
        metrics_data = []
        for metric_type in metric_types:
            metrics = quality_control.get_historical_metrics(
                metric_type=metric_type,
                entity_type=entity_type,
                days=30  # Last 30 days
            )
            if metrics:
                metrics_data.extend(metrics)
        
        if not metrics_data:
            raise HTTPException(status_code=404, detail="No metric data available")
        
        # Convert to DataFrame
        df = pd.DataFrame(metrics_data)
        
        # Pivot data to get metric values by timestamp
        pivot_df = df.pivot(index='timestamp', columns='metric_type', values='value')
        
        # Calculate correlation matrix
        corr_matrix = pivot_df.corr()
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmin=-1,
            zmax=1
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Quality Metrics Correlation Matrix for {entity_type}",
            xaxis_title="Metric Type",
            yaxis_title="Metric Type",
            template="plotly_white"
        )
        
        return {"plot": fig.to_json()}
        
    except Exception as e:
        logger.error(f"Error generating quality correlation visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate/batch")
async def validate_entity_batch(
    entity_type: EntityType,
    domain: Optional[FinancialDomain] = None,
    update_quality_metrics: bool = True,
    batch_size: int = 100
):
    """Validate a batch of entities"""
    try:
        # Get all entities of the specified type
        entities = neo4j_service.get_entities(entity_type)
        if not entities:
            raise HTTPException(status_code=404, detail=f"No entities found of type {entity_type}")
        
        # Perform batch validation
        result = await validation_pipeline.validate_entity_batch(
            entities=entities,
            domain=domain,
            update_quality_metrics=update_quality_metrics,
            batch_size=batch_size
        )
        
        return {
            "status": "success",
            "result": {
                "total_entities": result.total_entities,
                "processed_entities": result.processed_entities,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "success_count": result.success_count,
                "average_confidence": result.average_confidence,
                "processing_time": result.processing_time,
                "validation_reports": [report.dict() for report in result.validation_reports],
                "quality_metrics": result.quality_metrics
            }
        }
        
    except Exception as e:
        logger.error(f"Error in batch validation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate/batch/correct")
async def correct_entity_batch(
    entity_type: EntityType,
    auto_apply: bool = False,
    batch_size: int = 100
):
    """Apply corrections to a batch of entities"""
    try:
        # Get all entities of the specified type
        entities = neo4j_service.get_entities(entity_type)
        if not entities:
            raise HTTPException(status_code=404, detail=f"No entities found of type {entity_type}")
        
        # First validate the entities
        validation_result = await validation_pipeline.validate_entity_batch(
            entities=entities,
            batch_size=batch_size
        )
        
        # Then apply corrections
        correction_result = await validation_pipeline.correct_entity_batch(
            entities=entities,
            validation_reports=validation_result.validation_reports,
            auto_apply=auto_apply,
            batch_size=batch_size
        )
        
        return {
            "status": "success",
            "result": {
                "total_entities": correction_result.total_entities,
                "processed_entities": correction_result.processed_entities,
                "corrected_entities": correction_result.corrected_entities,
                "failed_corrections": correction_result.failed_corrections,
                "success_rate": correction_result.success_rate,
                "processing_time": correction_result.processing_time,
                "correction_details": correction_result.correction_details
            }
        }
        
    except Exception as e:
        logger.error(f"Error in batch correction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/batch/status/{batch_id}")
async def get_batch_validation_status(batch_id: str):
    """Get the status of a batch validation operation"""
    try:
        # Get batch status from Redis
        status = quality_control.get_batch_status(batch_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"No batch found with ID {batch_id}")
        
        return {
            "status": "success",
            "result": status
        }
        
    except Exception as e:
        logger.error(f"Error getting batch status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/batch/history")
async def get_batch_validation_history(
    entity_type: Optional[EntityType] = None,
    days: int = 30
):
    """Get history of batch validation operations"""
    try:
        # Get batch history from Redis
        history = quality_control.get_batch_history(
            entity_type=entity_type,
            days=days
        )
        
        return {
            "status": "success",
            "result": history
        }
        
    except Exception as e:
        logger.error(f"Error getting batch history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate/batch/summary")
async def get_batch_validation_summary(
    entity_type: Optional[EntityType] = None,
    days: int = 30
):
    """Get summary of batch validation operations"""
    try:
        # Get batch summary from Redis
        summary = quality_control.get_batch_summary(
            entity_type=entity_type,
            days=days
        )
        
        return {
            "status": "success",
            "result": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting batch summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/heatmap")
async def visualize_quality_heatmap(
    entity_type: Optional[str] = None,
    days: int = 30,
    metric_types: Optional[List[str]] = None
):
    """Generate a heatmap visualization of quality metrics."""
    try:
        # Get historical metrics
        metrics = await quality_control.get_historical_metrics(
            entity_type=entity_type,
            days=days,
            metric_types=metric_types
        )
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics found")
        
        # Process data for heatmap
        df = pd.DataFrame(metrics)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day_name()
        
        # Create pivot table for heatmap
        pivot = df.pivot_table(
            values='value',
            index='day',
            columns='hour',
            aggfunc='mean'
        )
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='Viridis',
            colorbar=dict(title='Quality Score')
        ))
        
        fig.update_layout(
            title='Quality Metrics Heatmap by Hour and Day',
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            template='plotly_white'
        )
        
        return JSONResponse(content=fig.to_json())
    except Exception as e:
        logger.error(f"Error generating quality heatmap: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/3d")
async def visualize_quality_3d(
    entity_type: Optional[str] = None,
    days: int = 30,
    metric_types: Optional[List[str]] = None
):
    """Generate a 3D visualization of quality metrics."""
    try:
        # Get historical metrics
        metrics = await quality_control.get_historical_metrics(
            entity_type=entity_type,
            days=days,
            metric_types=metric_types
        )
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics found")
        
        # Process data for 3D plot
        df = pd.DataFrame(metrics)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create 3D scatter plot
        fig = go.Figure(data=[go.Scatter3d(
            x=df['timestamp'],
            y=df['metric_type'],
            z=df['value'],
            mode='markers',
            marker=dict(
                size=8,
                color=df['value'],
                colorscale='Viridis',
                opacity=0.8
            )
        )])
        
        fig.update_layout(
            title='3D Quality Metrics Visualization',
            scene=dict(
                xaxis_title='Time',
                yaxis_title='Metric Type',
                zaxis_title='Value'
            ),
            template='plotly_white'
        )
        
        return JSONResponse(content=fig.to_json())
    except Exception as e:
        logger.error(f"Error generating 3D visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/sunburst")
async def visualize_quality_sunburst(
    entity_type: Optional[str] = None,
    days: int = 30
):
    """Generate a sunburst chart of quality metrics hierarchy."""
    try:
        # Get quality metrics
        metrics = await quality_control.get_quality_metrics(entity_type)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics found")
        
        # Process data for sunburst
        ids = []
        labels = []
        parents = []
        values = []
        
        for metric in metrics:
            # Add metric type
            ids.append(f"type_{metric.metric_type}")
            labels.append(metric.metric_type)
            parents.append("")
            values.append(metric.value)
            
            # Add entity type
            ids.append(f"entity_{metric.entity_type}")
            labels.append(metric.entity_type)
            parents.append(f"type_{metric.metric_type}")
            values.append(metric.value)
            
            # Add specific metric
            ids.append(f"metric_{metric.metric_type}_{metric.entity_type}")
            labels.append(f"{metric.metric_type} - {metric.entity_type}")
            parents.append(f"entity_{metric.entity_type}")
            values.append(metric.value)
        
        # Create sunburst chart
        fig = go.Figure(go.Sunburst(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total"
        ))
        
        fig.update_layout(
            title='Quality Metrics Hierarchy',
            template='plotly_white'
        )
        
        return JSONResponse(content=fig.to_json())
    except Exception as e:
        logger.error(f"Error generating sunburst chart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/parallel")
async def visualize_quality_parallel(
    entity_type: Optional[str] = None,
    days: int = 30,
    metric_types: Optional[List[str]] = None
):
    """Generate a parallel coordinates plot of quality metrics."""
    try:
        # Get historical metrics
        metrics = await quality_control.get_historical_metrics(
            entity_type=entity_type,
            days=days,
            metric_types=metric_types
        )
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics found")
        
        # Process data for parallel coordinates
        df = pd.DataFrame(metrics)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create parallel coordinates plot
        fig = go.Figure(data=
            go.Parcoords(
                line=dict(
                    color=df['value'],
                    colorscale='Viridis'
                ),
                dimensions=[
                    dict(range=[df['timestamp'].min(), df['timestamp'].max()],
                         label='Time', values=df['timestamp']),
                    dict(range=[0, 1],
                         label='Value', values=df['value']),
                    dict(tickvals=list(range(len(df['metric_type'].unique()))),
                         ticktext=df['metric_type'].unique(),
                         label='Metric Type',
                         values=df['metric_type'].astype('category').cat.codes)
                ]
            )
        )
        
        fig.update_layout(
            title='Quality Metrics Parallel Coordinates',
            template='plotly_white'
        )
        
        return JSONResponse(content=fig.to_json())
    except Exception as e:
        logger.error(f"Error generating parallel coordinates plot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/network")
async def visualize_quality_network(
    entity_type: Optional[str] = None,
    days: int = 30
):
    """Generate a network graph of quality metrics relationships."""
    try:
        # Get quality metrics and correlations
        metrics = await quality_control.get_quality_metrics(entity_type)
        correlations = await quality_control.get_metric_correlations(entity_type)
        
        if not metrics or not correlations:
            raise HTTPException(status_code=404, detail="No metrics or correlations found")
        
        # Create network graph
        G = nx.Graph()
        
        # Add nodes (metrics)
        for metric in metrics:
            G.add_node(
                metric.metric_type,
                value=metric.value,
                entity_type=metric.entity_type
            )
        
        # Add edges (correlations)
        for corr in correlations:
            if abs(corr.correlation) > 0.5:  # Only show strong correlations
                G.add_edge(
                    corr.metric1,
                    corr.metric2,
                    weight=abs(corr.correlation)
                )
        
        # Create network visualization
        pos = nx.spring_layout(G)
        
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += (x0, x1, None)
            edge_trace['y'] += (y0, y1, None)
        
        node_trace = go.Scatter(
            x=[],
            y=[],
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='Viridis',
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Node Value',
                    xanchor='left',
                    titleside='right'
                )
            )
        )
        
        for node in G.nodes():
            x, y = pos[node]
            node_trace['x'] += (x,)
            node_trace['y'] += (y,)
        
        node_trace['marker']['color'] = [G.nodes[node]['value'] for node in G.nodes()]
        node_trace['text'] = [f"{node}<br>Value: {G.nodes[node]['value']:.2f}" for node in G.nodes()]
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Quality Metrics Network',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20, l=5, r=5, t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                       ))
        
        return JSONResponse(content=fig.to_json())
    except Exception as e:
        logger.error(f"Error generating network graph: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualize/quality/dashboard")
async def visualize_quality_dashboard(
    entity_type: Optional[str] = None,
    days: int = 30
):
    """Generate a comprehensive dashboard of quality metrics."""
    try:
        # Get all necessary data
        metrics = await quality_control.get_quality_metrics(entity_type)
        historical_metrics = await quality_control.get_historical_metrics(
            entity_type=entity_type,
            days=days
        )
        correlations = await quality_control.get_metric_correlations(entity_type)
        anomalies = await quality_control.get_anomalies(entity_type)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics found")
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Quality Metrics Overview',
                'Historical Trends',
                'Metric Correlations',
                'Anomaly Detection',
                'Metric Distribution',
                'Quality Score Breakdown'
            )
        )
        
        # 1. Quality Metrics Overview (Bar Chart)
        df_metrics = pd.DataFrame([m.dict() for m in metrics])
        fig.add_trace(
            go.Bar(
                x=df_metrics['metric_type'],
                y=df_metrics['value'],
                name='Current Values'
            ),
            row=1, col=1
        )
        
        # 2. Historical Trends (Line Chart)
        df_historical = pd.DataFrame(historical_metrics)
        df_historical['timestamp'] = pd.to_datetime(df_historical['timestamp'])
        for metric_type in df_historical['metric_type'].unique():
            df_type = df_historical[df_historical['metric_type'] == metric_type]
            fig.add_trace(
                go.Scatter(
                    x=df_type['timestamp'],
                    y=df_type['value'],
                    name=metric_type
                ),
                row=1, col=2
            )
        
        # 3. Metric Correlations (Heatmap)
        corr_matrix = pd.DataFrame(correlations).pivot(
            index='metric1',
            columns='metric2',
            values='correlation'
        )
        fig.add_trace(
            go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale='RdBu'
            ),
            row=2, col=1
        )
        
        # 4. Anomaly Detection (Scatter Plot)
        df_anomalies = pd.DataFrame(anomalies)
        fig.add_trace(
            go.Scatter(
                x=df_anomalies['timestamp'],
                y=df_anomalies['value'],
                mode='markers',
                marker=dict(
                    color=df_anomalies['is_anomaly'].map({True: 'red', False: 'blue'}),
                    size=10
                ),
                name='Anomalies'
            ),
            row=2, col=2
        )
        
        # 5. Metric Distribution (Box Plot)
        for metric_type in df_historical['metric_type'].unique():
            df_type = df_historical[df_historical['metric_type'] == metric_type]
            fig.add_trace(
                go.Box(
                    y=df_type['value'],
                    name=metric_type
                ),
                row=3, col=1
            )
        
        # 6. Quality Score Breakdown (Pie Chart)
        fig.add_trace(
            go.Pie(
                labels=df_metrics['metric_type'],
                values=df_metrics['value'],
                hole=0.4
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=1200,
            width=1600,
            title_text="Quality Metrics Dashboard",
            showlegend=True,
            template='plotly_white'
        )
        
        return JSONResponse(content=fig.to_json())
    except Exception as e:
        logger.error(f"Error generating quality dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Existing process endpoint

# Existing process endpoint
@router.post("/process")
async def process_data(data: Dict[str, Any]):
    """Process financial data and update the knowledge graph"""
    try:
        # Process the data using our services
        result = validation_service.process_data(data)
        return {"status": "success", "message": "Data processed successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# New validation endpoints
@router.post("/documents/{document_id}/validate", response_model=ValidationResponse)
async def validate_document(document_id: str, request: ValidationRequest):
    """Validate a specific document against validation rules"""
    try:
        # Use document_id from path parameter, not request body
        doc_path = os.path.join("data", document_id)
        if not os.path.exists(doc_path):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Find the document file
        doc_files = [f for f in os.listdir(doc_path) if f.endswith('.pdf')]
        if not doc_files:
            raise HTTPException(status_code=404, detail="No PDF file found in document")
        
        file_path = os.path.join(doc_path, doc_files[0])
        
        # Perform validation - create a simple document validation
        validation_results = []
        
        # Basic document validation
        try:
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                validation_results.append(ValidationResult(
                    rule_name="document_accessibility",
                    level=ValidationLevel.ERROR,
                    message="Document file not found or not accessible",
                    details={"file_path": file_path}
                ))
            else:
                # Check file size
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    validation_results.append(ValidationResult(
                        rule_name="document_content",
                        level=ValidationLevel.ERROR,
                        message="Document file is empty",
                        details={"file_size": file_size}
                    ))
                elif file_size > 50 * 1024 * 1024:  # 50MB limit
                    validation_results.append(ValidationResult(
                        rule_name="document_size",
                        level=ValidationLevel.WARNING,
                        message="Document file is very large",
                        details={"file_size": file_size, "size_mb": file_size / (1024 * 1024)}
                    ))
                else:
                    validation_results.append(ValidationResult(
                        rule_name="document_accessibility",
                        level=ValidationLevel.INFO,
                        message="Document file is accessible and valid",
                        details={"file_path": file_path, "file_size": file_size}
                    ))
                
                # Check if it's a PDF
                if not file_path.lower().endswith('.pdf'):
                    validation_results.append(ValidationResult(
                        rule_name="document_format",
                        level=ValidationLevel.WARNING,
                        message="Document is not a PDF file",
                        details={"file_path": file_path}
                    ))
                else:
                    validation_results.append(ValidationResult(
                        rule_name="document_format",
                        level=ValidationLevel.INFO,
                        message="Document is a valid PDF file",
                        details={"file_path": file_path}
                    ))
                    
        except Exception as e:
            validation_results.append(ValidationResult(
                rule_name="document_validation",
                level=ValidationLevel.ERROR,
                message=f"Error during document validation: {str(e)}",
                details={"error": str(e)}
            ))
        
        # Generate summary
        summary = {
            "total_rules": len(validation_results),
            "passed": len([r for r in validation_results if r.status == "PASS"]),
            "failed": len([r for r in validation_results if r.status == "FAIL"]),
            "warnings": len([r for r in validation_results if r.status == "WARNING"])
        }
        
        return ValidationResponse(
            document_id=document_id,
            validation_results=validation_results,
            summary=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")



# Graph visualization endpoints
@router.get("/graph/{document_id}", response_model=GraphDataResponse)
async def get_graph_data(document_id: str, request: GraphDataRequest = Depends()):
    """Get graph data for visualization"""
    try:
        # Get graph data from Neo4j
        graph_data = neo4j_service.get_graph_data(document_id, request.max_nodes)
        
        # Convert to visualization format
        nodes = []
        edges = []
        
        # Add entities as nodes
        for entity in graph_data.get("entities", []):
            nodes.append({
                "id": entity.get("id", str(uuid.uuid4())),
                "label": entity.get("properties", {}).get("name", entity.get("text", "Unknown")),
                "type": entity.get("type", "UNKNOWN"),
                "properties": entity.get("properties", {}),
                "confidence": entity.get("confidence", 0.0)
            })
        
        # Add relationships as edges
        for rel in graph_data.get("relationships", []):
            edges.append({
                "id": rel.get("id", str(uuid.uuid4())),
                "source": rel.get("source_id"),
                "target": rel.get("target_id"),
                "type": rel.get("type", "UNKNOWN"),
                "properties": rel.get("properties", {}),
                "confidence": rel.get("confidence", 0.0)
            })
        
        metadata = {
            "document_id": document_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return GraphDataResponse(
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Failed to get graph data for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {str(e)}")

@router.get("/graph/nodes/{node_id}")
async def get_node_details(node_id: str):
    """Get detailed information about a specific node"""
    try:
        node_data = neo4j_service.get_node_details(node_id)
        return node_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node details: {str(e)}")

@router.get("/graph/nodes/{node_id}/relationships")
async def get_node_relationships(node_id: str):
    """Get relationships for a specific node"""
    try:
        relationships = neo4j_service.get_node_relationships(node_id)
        return {"node_id": node_id, "relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node relationships: {str(e)}")

# Correction management endpoints
@router.post("/documents/{document_id}/corrections", response_model=CorrectionResponse)
async def create_correction(document_id: str, request: CorrectionRequest):
    """Create a correction for a validation issue"""
    try:
        correction_id = str(uuid.uuid4())
        
        # Apply correction strategy
        applied_changes = quality_control.apply_correction(
            document_id, 
            request.validation_result_id, 
            request.strategy
        )
        
        return CorrectionResponse(
            correction_id=correction_id,
            document_id=document_id,
            status="APPLIED",
            applied_changes=applied_changes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create correction: {str(e)}")

@router.get("/documents/{document_id}/corrections")
async def get_document_corrections(document_id: str):
    """Get all corrections for a document"""
    try:
        corrections = quality_control.get_document_corrections(document_id)
        return {"document_id": document_id, "corrections": corrections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get corrections: {str(e)}")

@router.post("/documents/{document_id}/corrections/{correction_id}/apply")
async def apply_correction(document_id: str, correction_id: str):
    """Apply a specific correction"""
    try:
        result = quality_control.apply_correction_by_id(document_id, correction_id)
        return {"status": "success", "correction_id": correction_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply correction: {str(e)}")

# Validation rules management
@router.get("/validation/rules")
async def get_validation_rules():
    """Get all available validation rules"""
    try:
        rules = validation_service.get_all_rules()
        return {"rules": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation rules: {str(e)}")

@router.post("/validation/rules")
async def create_validation_rule(rule: ValidationRule):
    """Create a new validation rule"""
    try:
        created_rule = validation_service.create_rule(rule)
        return {"status": "success", "rule": created_rule}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create validation rule: {str(e)}")

@router.put("/validation/rules/{rule_id}")
async def update_validation_rule(rule_id: str, rule: ValidationRule):
    """Update an existing validation rule"""
    try:
        updated_rule = validation_service.update_rule(rule_id, rule)
        return {"status": "success", "rule": updated_rule}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update validation rule: {str(e)}")

@router.delete("/validation/rules/{rule_id}")
async def delete_validation_rule(rule_id: str):
    """Delete a validation rule"""
    try:
        validation_service.delete_rule(rule_id)
        return {"status": "success", "message": f"Rule {rule_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete validation rule: {str(e)}") 