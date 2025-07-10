from typing import Dict, List, Any, Optional
import spacy
import re
from dataclasses import dataclass
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

@dataclass
class FinancialEntity:
    id: str
    text: str
    type: str
    confidence: float
    page: int
    position: Dict[str, Any]
    metadata: Dict[str, Any]

class FinancialEntityRecognizer:
    def __init__(self):
        # Load English language model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded spaCy model")
        except OSError:
            logger.warning("Downloading spaCy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Add financial entity patterns
        self._add_financial_patterns()
        
        # Define financial entity types
        self.entity_types = {
            "COMPANY": "Company or organization name",
            "PERSON": "Person name",
            "CURRENCY": "Monetary value",
            "PERCENTAGE": "Percentage value",
            "DATE": "Date or time period",
            "FINANCIAL_METRIC": "Financial metric or KPI",
            "ACCOUNT": "Financial account or category",
            "TRANSACTION": "Financial transaction",
            "MARKET": "Market or exchange",
            "INDUSTRY": "Industry or sector"
        }

    def _add_financial_patterns(self):
        """Add custom financial entity patterns to the pipeline"""
        ruler = self.nlp.add_pipe("entity_ruler")
        
        patterns = [
            # Financial metrics
            {"label": "FINANCIAL_METRIC", "pattern": [
                {"LOWER": {"IN": ["revenue", "income", "profit", "loss", "earnings", "expenses"]}},
                {"LOWER": {"IN": ["growth", "margin", "ratio", "rate"]}, "OP": "?"}
            ]},
            {"label": "FINANCIAL_METRIC", "pattern": [
                {"LOWER": {"IN": ["ebitda", "roi", "roe", "roa", "eps", "pe"]}}
            ]},
            
            # Currency patterns
            {"label": "CURRENCY", "pattern": [
                {"TEXT": {"REGEX": r"[$€£¥]"},
                 "OP": "?"},
                {"LIKE_NUM": True},
                {"LOWER": {"IN": ["million", "billion", "trillion"]}, "OP": "?"}
            ]},
            
            # Percentage patterns
            {"label": "PERCENTAGE", "pattern": [
                {"LIKE_NUM": True},
                {"TEXT": "%"}
            ]},
            
            # Account patterns
            {"label": "ACCOUNT", "pattern": [
                {"LOWER": {"IN": ["cash", "accounts", "inventory", "assets", "liabilities"]}},
                {"LOWER": {"IN": ["receivable", "payable", "equity", "capital"]}, "OP": "?"}
            ]},
            
            # Transaction patterns
            {"label": "TRANSACTION", "pattern": [
                {"LOWER": {"IN": ["purchase", "sale", "payment", "receipt", "transfer"]}},
                {"LOWER": {"IN": ["order", "invoice", "receipt", "transaction"]}, "OP": "?"}
            ]},
            
            # Market patterns
            {"label": "MARKET", "pattern": [
                {"LOWER": {"IN": ["nyse", "nasdaq", "lse", "tsx", "asx"]}}
            ]},
            
            # Industry patterns
            {"label": "INDUSTRY", "pattern": [
                {"LOWER": {"IN": ["technology", "finance", "healthcare", "manufacturing", "retail"]}},
                {"LOWER": {"IN": ["sector", "industry", "market"]}, "OP": "?"}
            ]}
        ]
        
        ruler.add_patterns(patterns)

    def extract_entities(self, text: str, page: int = 0) -> List[FinancialEntity]:
        """
        Extract financial entities from text
        """
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Skip non-financial entities
            if ent.label_ not in self.entity_types:
                continue
            
            # Calculate confidence based on entity type and context
            confidence = self._calculate_confidence(ent)
            
            # Create entity object
            entity = FinancialEntity(
                id=str(uuid.uuid4()),
                text=ent.text,
                type=ent.label_,
                confidence=confidence,
                page=page,
                position={
                    "start": ent.start_char,
                    "end": ent.end_char
                },
                metadata={
                    "context": text[max(0, ent.start_char - 50):min(len(text), ent.end_char + 50)],
                    "detected_at": datetime.now().isoformat()
                }
            )
            entities.append(entity)
        
        return entities

    def _calculate_confidence(self, entity: spacy.tokens.Span) -> float:
        """
        Calculate confidence score for an entity based on various factors
        """
        base_confidence = 0.7  # Base confidence score
        
        # Adjust confidence based on entity type
        if entity.label_ in ["CURRENCY", "PERCENTAGE"]:
            base_confidence += 0.2  # High confidence for well-defined patterns
        elif entity.label_ in ["COMPANY", "PERSON"]:
            base_confidence += 0.1  # Medium confidence for named entities
        
        # Adjust confidence based on context
        if entity.text[0].isupper():
            base_confidence += 0.1  # Higher confidence for capitalized entities
        
        # Adjust confidence based on length
        if len(entity.text) > 3:
            base_confidence += 0.05  # Slightly higher confidence for longer entities
        
        return min(base_confidence, 1.0)  # Cap at 1.0

    def get_entity_types(self) -> Dict[str, str]:
        """Get list of supported entity types and their descriptions"""
        return self.entity_types

    def get_entity_statistics(self, entities: List[FinancialEntity]) -> Dict[str, Any]:
        """Get statistics about extracted entities"""
        stats = {
            "total_entities": len(entities),
            "entities_by_type": {},
            "average_confidence": 0.0,
            "entities_by_page": {}
        }
        
        if not entities:
            return stats
        
        # Calculate statistics
        total_confidence = 0
        for entity in entities:
            # Count by type
            stats["entities_by_type"][entity.type] = stats["entities_by_type"].get(entity.type, 0) + 1
            
            # Count by page
            stats["entities_by_page"][entity.page] = stats["entities_by_page"].get(entity.page, 0) + 1
            
            # Sum confidence
            total_confidence += entity.confidence
        
        # Calculate average confidence
        stats["average_confidence"] = total_confidence / len(entities)
        
        return stats 