from celery import Celery
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime, timedelta
import uuid
import numpy as np
from collections import defaultdict
from app.models.graph_models import Entity, Relationship, EntityType, RelationshipType
from app.services.neo4j_service import Neo4jService
from app.services.entity_recognition import FinancialEntityRecognizer
from app.services.relationship_extraction import RelationshipExtractor
from app.services.status_tracker import StatusTracker, ProcessingStatus, ProcessingStage

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'finance_knowledge_graph',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1
)

# Export the celery app instance
app = celery_app

class DocumentProcessor:
    def __init__(
        self,
        neo4j_service: Neo4jService,
        entity_recognizer: FinancialEntityRecognizer,
        relationship_extractor: RelationshipExtractor,
        status_tracker: StatusTracker
    ):
        self.neo4j_service = neo4j_service
        self.entity_recognizer = entity_recognizer
        self.relationship_extractor = relationship_extractor
        self.status_tracker = status_tracker

    def process_document(self, document_id: str, text: str) -> Dict[str, Any]:
        """Process a document and extract entities and relationships"""
        try:
            # Update status to entity extraction
            self.status_tracker.update_status(
                document_id,
                status=ProcessingStatus.PROCESSING,
                stage=ProcessingStage.ENTITY_EXTRACTION,
                progress=0.2
            )
            
            # Extract entities
            entities = self.entity_recognizer.extract_entities(text)
            
            # Update status to relationship extraction
            self.status_tracker.update_status(
                document_id,
                status=ProcessingStatus.PROCESSING,
                stage=ProcessingStage.RELATIONSHIP_EXTRACTION,
                progress=0.4
            )
            
            # Create entity nodes
            entity_nodes = {}
            for entity in entities:
                entity_node = Entity(
                    id=str(uuid.uuid4()),
                    type=EntityType(entity.type),
                    name=entity.text,
                    properties={
                        "text": entity.text,
                        "page": entity.position.get("page", 0),
                        "position": entity.position
                    },
                    confidence=entity.confidence,
                    source_document=document_id,
                    metadata=entity.metadata
                )
                entity_id = self.neo4j_service.create_entity(entity_node)
                entity_nodes[entity.text] = entity_id
            
            # Extract relationships
            relationships = self.relationship_extractor.extract_relationships(text)
            
            # Update status to graph storage
            self.status_tracker.update_status(
                document_id,
                status=ProcessingStatus.PROCESSING,
                stage=ProcessingStage.GRAPH_STORAGE,
                progress=0.6
            )
            
            # Create relationship edges
            relationship_edges = []
            for rel in relationships:
                if rel.source_id in entity_nodes and rel.target_id in entity_nodes:
                    relationship = Relationship(
                        id=str(uuid.uuid4()),
                        type=RelationshipType(rel.type),
                        source_id=entity_nodes[rel.source_id],
                        target_id=entity_nodes[rel.target_id],
                        properties=rel.properties,
                        confidence=rel.confidence,
                        source_document=document_id,
                        metadata=rel.metadata
                    )
                    relationship_id = self.neo4j_service.create_relationship(relationship)
                    relationship_edges.append(relationship_id)
            
            # Update status to completed
            self.status_tracker.update_status(
                document_id,
                status=ProcessingStatus.COMPLETED,
                stage=ProcessingStage.METRICS_CALCULATION,
                progress=1.0,
                entities_processed=len(entities),
                relationships_processed=len(relationships)
            )
            
            return {
                "status": "success",
                "document_id": document_id,
                "entities_processed": len(entities),
                "relationships_processed": len(relationships),
                "entity_nodes": len(entity_nodes),
                "relationship_edges": len(relationship_edges),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            self.status_tracker.update_status(
                document_id,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
            return {
                "status": "error",
                "document_id": document_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

@celery_app.task(bind=True)
def process_document_task(
    self,
    document_id: str,
    text: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str
) -> Dict[str, Any]:
    """Celery task for document processing"""
    try:
        # Initialize services
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        entity_recognizer = FinancialEntityRecognizer()
        relationship_extractor = RelationshipExtractor()
        status_tracker = StatusTracker()
        
        # Create processor
        processor = DocumentProcessor(
            neo4j_service=neo4j_service,
            entity_recognizer=entity_recognizer,
            relationship_extractor=relationship_extractor,
            status_tracker=status_tracker
        )
        
        # Process document
        result = processor.process_document(document_id, text)
        
        # Update task status
        self.update_state(
            state='SUCCESS',
            meta={
                'status': result['status'],
                'document_id': document_id,
                'entities_processed': result.get('entities_processed', 0),
                'relationships_processed': result.get('relationships_processed', 0),
                'timestamp': result['timestamp']
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in process_document_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'document_id': document_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def analyze_entity_network_task(
    self,
    entity_id: str,
    depth: int = 2,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """Analyze the network of relationships around an entity"""
    try:
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get entity subgraph
        subgraph = neo4j_service.get_entity_subgraph(entity_id, depth)
        
        # Calculate network metrics
        metrics = {
            "total_entities": len(subgraph.nodes),
            "total_relationships": len(subgraph.relationships),
            "average_degree": sum(len(node.relationships) for node in subgraph.nodes) / len(subgraph.nodes) if subgraph.nodes else 0,
            "relationship_types": {},
            "entity_types": {}
        }
        
        # Count relationship types
        for rel in subgraph.relationships:
            metrics["relationship_types"][rel.type] = metrics["relationship_types"].get(rel.type, 0) + 1
            
        # Count entity types
        for node in subgraph.nodes:
            metrics["entity_types"][node.type] = metrics["entity_types"].get(node.type, 0) + 1
            
        return {
            "status": "success",
            "entity_id": entity_id,
            "depth": depth,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_entity_network_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'entity_id': entity_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def find_similar_entities_task(
    self,
    entity_id: str,
    similarity_threshold: float = 0.7,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """Find similar entities based on properties and relationships"""
    try:
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get entity
        entity = neo4j_service.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
            
        # Find similar entities
        similar_entities = []
        for other_entity in neo4j_service.get_all_entities():
            if other_entity.id != entity_id:
                # Calculate similarity score
                similarity = neo4j_service.calculate_entity_similarity(entity, other_entity)
                if similarity >= similarity_threshold:
                    similar_entities.append({
                        "entity_id": other_entity.id,
                        "name": other_entity.name,
                        "type": other_entity.type,
                        "similarity_score": similarity
                    })
                    
        return {
            "status": "success",
            "entity_id": entity_id,
            "similarity_threshold": similarity_threshold,
            "similar_entities": sorted(similar_entities, key=lambda x: x["similarity_score"], reverse=True),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in find_similar_entities_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'entity_id': entity_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def analyze_relationship_patterns_task(
    self,
    entity_type: str,
    relationship_type: str,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """Analyze patterns in relationships of a specific type"""
    try:
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get relationships
        relationships = neo4j_service.get_relationships_by_type(relationship_type)
        
        # Filter by entity type
        filtered_relationships = [
            rel for rel in relationships
            if neo4j_service.get_entity(rel.source_id).type == entity_type
        ]
        
        # Analyze patterns
        patterns = {
            "total_relationships": len(filtered_relationships),
            "unique_target_types": {},
            "property_distributions": {},
            "confidence_distribution": {
                "min": min(rel.confidence for rel in filtered_relationships),
                "max": max(rel.confidence for rel in filtered_relationships),
                "avg": sum(rel.confidence for rel in filtered_relationships) / len(filtered_relationships)
            },
            "temporal_distribution": {
                "earliest": min(rel.created_at for rel in filtered_relationships),
                "latest": max(rel.created_at for rel in filtered_relationships)
            }
        }
        
        # Count target types
        for rel in filtered_relationships:
            target_type = neo4j_service.get_entity(rel.target_id).type
            patterns["unique_target_types"][target_type] = patterns["unique_target_types"].get(target_type, 0) + 1
            
        # Analyze property distributions
        for rel in filtered_relationships:
            for key, value in rel.properties.items():
                if key not in patterns["property_distributions"]:
                    patterns["property_distributions"][key] = {}
                if value not in patterns["property_distributions"][key]:
                    patterns["property_distributions"][key][value] = 0
                patterns["property_distributions"][key][value] += 1
                
        return {
            "status": "success",
            "entity_type": entity_type,
            "relationship_type": relationship_type,
            "patterns": patterns,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_relationship_patterns_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'entity_type': entity_type,
                'relationship_type': relationship_type,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def update_entity_task(
    self,
    entity_id: str,
    properties: Dict[str, Any],
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str
) -> Dict[str, Any]:
    """Celery task for updating entity properties"""
    try:
        # Initialize Neo4j service
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get existing entity
        entity = neo4j_service.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        # Update properties
        entity.properties.update(properties)
        entity.updated_at = datetime.utcnow()
        
        # Save changes
        success = neo4j_service.update_entity(entity)
        
        return {
            "status": "success" if success else "error",
            "entity_id": entity_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in update_entity_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'entity_id': entity_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def merge_entities_task(
    self,
    entity1_id: str,
    entity2_id: str,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str
) -> Dict[str, Any]:
    """Celery task for merging entities"""
    try:
        # Initialize Neo4j service
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Merge entities
        merged_id = neo4j_service.merge_entities(entity1_id, entity2_id)
        
        return {
            "status": "success",
            "entity1_id": entity1_id,
            "entity2_id": entity2_id,
            "merged_id": merged_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in merge_entities_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'entity1_id': entity1_id,
                'entity2_id': entity2_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def get_graph_metrics_task(
    self,
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str
) -> Dict[str, Any]:
    """Celery task for getting graph metrics"""
    try:
        # Initialize Neo4j service
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get metrics
        metrics = neo4j_service.get_graph_metrics()
        
        return {
            "status": "success",
            "metrics": metrics.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_graph_metrics_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def analyze_financial_metrics_task(
    self,
    entity_id: str,
    time_period: str = "1y",
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """Analyze financial metrics for an entity over time"""
    try:
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get entity
        entity = neo4j_service.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
            
        # Get financial metrics relationships
        metrics = neo4j_service.get_relationships_by_type("HAS_METRIC")
        metrics = [m for m in metrics if m.source_id == entity_id]
        
        # Group metrics by type and time
        metric_groups = defaultdict(list)
        for metric in metrics:
            metric_type = metric.properties.get("type")
            timestamp = metric.properties.get("timestamp")
            value = metric.properties.get("value")
            if metric_type and timestamp and value:
                metric_groups[metric_type].append((timestamp, float(value)))
                
        # Calculate trends and statistics
        analysis = {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "time_period": time_period,
            "metrics": {}
        }
        
        for metric_type, values in metric_groups.items():
            if not values:
                continue
                
            # Sort by timestamp
            values.sort(key=lambda x: x[0])
            timestamps, values = zip(*values)
            
            # Calculate statistics
            analysis["metrics"][metric_type] = {
                "current_value": values[-1],
                "min_value": min(values),
                "max_value": max(values),
                "avg_value": np.mean(values),
                "std_dev": np.std(values),
                "trend": np.polyfit(range(len(values)), values, 1)[0],
                "growth_rate": (values[-1] - values[0]) / values[0] if values[0] != 0 else 0,
                "volatility": np.std(values) / np.mean(values) if np.mean(values) != 0 else 0,
                "timeline": {
                    "timestamps": timestamps,
                    "values": values
                }
            }
            
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_financial_metrics_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'entity_id': entity_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def analyze_company_relationships_task(
    self,
    company_id: str,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """Analyze relationships between companies and other entities"""
    try:
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get company
        company = neo4j_service.get_entity(company_id)
        if not company or company.type != EntityType.COMPANY:
            raise ValueError(f"Company {company_id} not found")
            
        # Get all relationships
        relationships = neo4j_service.get_entity_relationships(company_id)
        
        # Analyze relationships by type
        relationship_analysis = defaultdict(list)
        for rel in relationships:
            target = neo4j_service.get_entity(rel.target_id)
            if target:
                relationship_analysis[rel.type].append({
                    "target_id": target.id,
                    "target_name": target.name,
                    "target_type": target.type,
                    "confidence": rel.confidence,
                    "properties": rel.properties
                })
                
        # Calculate relationship metrics
        metrics = {
            "total_relationships": len(relationships),
            "relationship_types": {
                rel_type: len(rels)
                for rel_type, rels in relationship_analysis.items()
            },
            "target_types": defaultdict(int),
            "average_confidence": np.mean([r.confidence for r in relationships]),
            "relationship_details": dict(relationship_analysis)
        }
        
        # Count target types
        for rels in relationship_analysis.values():
            for rel in rels:
                metrics["target_types"][rel["target_type"]] += 1
                
        return {
            "status": "success",
            "company_id": company_id,
            "company_name": company.name,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_company_relationships_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'company_id': company_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def analyze_market_trends_task(
    self,
    industry: str,
    time_period: str = "1y",
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """Analyze market trends for a specific industry"""
    try:
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get companies in industry
        companies = neo4j_service.get_entities_by_type(EntityType.COMPANY)
        companies = [
            c for c in companies
            if c.properties.get("industry") == industry
        ]
        
        if not companies:
            raise ValueError(f"No companies found in industry {industry}")
            
        # Collect metrics for all companies
        industry_metrics = defaultdict(list)
        for company in companies:
            metrics = neo4j_service.get_relationships_by_type("HAS_METRIC")
            metrics = [m for m in metrics if m.source_id == company.id]
            
            for metric in metrics:
                metric_type = metric.properties.get("type")
                timestamp = metric.properties.get("timestamp")
                value = metric.properties.get("value")
                if metric_type and timestamp and value:
                    industry_metrics[metric_type].append({
                        "company_id": company.id,
                        "company_name": company.name,
                        "timestamp": timestamp,
                        "value": float(value)
                    })
                    
        # Analyze trends
        analysis = {
            "industry": industry,
            "time_period": time_period,
            "total_companies": len(companies),
            "metrics": {}
        }
        
        for metric_type, values in industry_metrics.items():
            if not values:
                continue
                
            # Group by timestamp
            timestamp_groups = defaultdict(list)
            for value in values:
                timestamp_groups[value["timestamp"]].append(value["value"])
                
            # Calculate industry averages
            timestamps = sorted(timestamp_groups.keys())
            averages = [
                np.mean(timestamp_groups[t])
                for t in timestamps
            ]
            
            analysis["metrics"][metric_type] = {
                "industry_average": np.mean(averages),
                "industry_trend": np.polyfit(range(len(averages)), averages, 1)[0],
                "volatility": np.std(averages) / np.mean(averages) if np.mean(averages) != 0 else 0,
                "company_rankings": sorted(
                    [
                        {
                            "company_id": v["company_id"],
                            "company_name": v["company_name"],
                            "latest_value": v["value"]
                        }
                        for v in values
                        if v["timestamp"] == timestamps[-1]
                    ],
                    key=lambda x: x["latest_value"],
                    reverse=True
                ),
                "timeline": {
                    "timestamps": timestamps,
                    "averages": averages
                }
            }
            
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_market_trends_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'industry': industry,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise

@celery_app.task(bind=True)
def analyze_risk_factors_task(
    self,
    entity_id: str,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """Analyze risk factors for an entity"""
    try:
        neo4j_service = Neo4jService(neo4j_uri, neo4j_user, neo4j_password)
        
        # Get entity
        entity = neo4j_service.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
            
        # Get risk-related relationships
        risk_relationships = [
            rel for rel in neo4j_service.get_entity_relationships(entity_id)
            if rel.type in [
                "HAS_RISK",
                "EXPOSED_TO",
                "DEPENDS_ON",
                "COMPETES_WITH"
            ]
        ]
        
        # Analyze risk factors
        risk_analysis = {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "entity_type": entity.type,
            "risk_factors": defaultdict(list),
            "risk_metrics": {
                "total_risks": len(risk_relationships),
                "risk_types": defaultdict(int),
                "average_confidence": np.mean([r.confidence for r in risk_relationships]),
                "risk_severity": defaultdict(int)
            }
        }
        
        # Process each risk relationship
        for rel in risk_relationships:
            target = neo4j_service.get_entity(rel.target_id)
            if not target:
                continue
                
            risk_factor = {
                "risk_id": target.id,
                "risk_name": target.name,
                "risk_type": target.type,
                "confidence": rel.confidence,
                "severity": rel.properties.get("severity", "medium"),
                "description": rel.properties.get("description", ""),
                "mitigation": rel.properties.get("mitigation", ""),
                "impact": rel.properties.get("impact", {})
            }
            
            risk_analysis["risk_factors"][rel.type].append(risk_factor)
            risk_analysis["risk_metrics"]["risk_types"][rel.type] += 1
            risk_analysis["risk_metrics"]["risk_severity"][risk_factor["severity"]] += 1
            
        # Calculate risk scores
        risk_analysis["risk_metrics"]["overall_risk_score"] = sum(
            len(factors) * {
                "high": 3,
                "medium": 2,
                "low": 1
            }.get(factors[0]["severity"], 1)
            for factors in risk_analysis["risk_factors"].values()
        )
        
        return {
            "status": "success",
            "analysis": risk_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_risk_factors_task: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'error',
                'entity_id': entity_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        raise 