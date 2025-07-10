from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from enum import Enum
from pydantic import BaseModel
import redis
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingStage(str, Enum):
    DOCUMENT_LOADING = "document_loading"
    ENTITY_EXTRACTION = "entity_extraction"
    RELATIONSHIP_EXTRACTION = "relationship_extraction"
    GRAPH_STORAGE = "graph_storage"
    METRICS_CALCULATION = "metrics_calculation"

class ProcessingMetrics(BaseModel):
    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    average_processing_time: float = 0.0
    last_updated: datetime = datetime.utcnow()
    
    # Enhanced metrics
    documents_by_status: Dict[str, int] = {}
    documents_by_stage: Dict[str, int] = {}
    entities_by_type: Dict[str, int] = {}
    relationships_by_type: Dict[str, int] = {}
    processing_times: Dict[str, List[float]] = {}
    error_counts: Dict[str, int] = {}
    success_rate: float = 0.0
    average_entities_per_document: float = 0.0
    average_relationships_per_document: float = 0.0
    processing_speed: float = 0.0  # documents per hour
    peak_processing_time: float = 0.0
    average_confidence: float = 0.0

class DocumentStatus(BaseModel):
    document_id: str
    status: ProcessingStatus
    current_stage: Optional[ProcessingStage] = None
    progress: float = 0.0
    entities_processed: int = 0
    relationships_processed: int = 0
    error_message: Optional[str] = None
    start_time: datetime = datetime.utcnow()
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    
    # Enhanced status fields
    stage_times: Dict[str, float] = {}
    entity_types: Dict[str, int] = {}
    relationship_types: Dict[str, int] = {}
    confidence_scores: Dict[str, float] = {}
    retry_count: int = 0
    last_error: Optional[str] = None
    processing_duration: Optional[float] = None

class StatusTracker:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize the status tracker with Redis connection"""
        self.redis_client = redis.from_url(redis_url)
        self.metrics_key = "processing_metrics"
        self.status_prefix = "doc_status:"
        self.stage_prefix = "stage_status:"
        self.history_prefix = "processing_history:"
        
    def _get_status_key(self, document_id: str) -> str:
        """Get Redis key for document status"""
        return f"{self.status_prefix}{document_id}"
        
    def _get_stage_key(self, document_id: str, stage: ProcessingStage) -> str:
        """Get Redis key for processing stage"""
        return f"{self.stage_prefix}{document_id}:{stage}"
        
    def _get_history_key(self, document_id: str) -> str:
        """Get Redis key for processing history"""
        return f"{self.history_prefix}{document_id}"
        
    def initialize_document(self, document_id: str, metadata: Dict[str, Any] = None) -> DocumentStatus:
        """Initialize tracking for a new document"""
        status = DocumentStatus(
            document_id=document_id,
            status=ProcessingStatus.PENDING,
            metadata=metadata or {}
        )
        
        # Store in Redis
        self.redis_client.set(
            self._get_status_key(document_id),
            status.json(),
            ex=86400  # Expire after 24 hours
        )
        
        # Initialize history
        self.redis_client.set(
            self._get_history_key(document_id),
            json.dumps([]),
            ex=86400
        )
        
        # Update metrics
        self._update_metrics(total_documents=1)
        
        return status
        
    def update_status(
        self,
        document_id: str,
        status: ProcessingStatus,
        stage: Optional[ProcessingStage] = None,
        progress: float = 0.0,
        entities_processed: int = 0,
        relationships_processed: int = 0,
        error_message: Optional[str] = None,
        entity_types: Optional[Dict[str, int]] = None,
        relationship_types: Optional[Dict[str, int]] = None,
        confidence_scores: Optional[Dict[str, float]] = None
    ) -> DocumentStatus:
        """Update the processing status of a document"""
        # Get current status
        current_status = self.get_status(document_id)
        if not current_status:
            raise ValueError(f"No status found for document {document_id}")
            
        # Update fields
        current_status.status = status
        if stage:
            current_status.current_stage = stage
            # Record stage time
            if stage not in current_status.stage_times:
                current_status.stage_times[stage] = datetime.utcnow().timestamp()
        current_status.progress = progress
        current_status.entities_processed = entities_processed
        current_status.relationships_processed = relationships_processed
        if error_message:
            current_status.error_message = error_message
            current_status.last_error = error_message
            current_status.retry_count += 1
        if entity_types:
            current_status.entity_types = entity_types
        if relationship_types:
            current_status.relationship_types = relationship_types
        if confidence_scores:
            current_status.confidence_scores = confidence_scores
            
        if status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            current_status.end_time = datetime.utcnow()
            if current_status.start_time:
                current_status.processing_duration = (
                    current_status.end_time - current_status.start_time
                ).total_seconds()
            
        # Store in Redis
        self.redis_client.set(
            self._get_status_key(document_id),
            current_status.json(),
            ex=86400
        )
        
        # Update history
        history = self._get_history(document_id)
        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "stage": stage,
            "progress": progress,
            "entities_processed": entities_processed,
            "relationships_processed": relationships_processed,
            "error_message": error_message
        })
        self.redis_client.set(
            self._get_history_key(document_id),
            json.dumps(history),
            ex=86400
        )
        
        # Update metrics
        if status == ProcessingStatus.COMPLETED:
            self._update_metrics(
                processed_documents=1,
                total_entities=entities_processed,
                total_relationships=relationships_processed,
                entity_types=entity_types,
                relationship_types=relationship_types,
                confidence_scores=confidence_scores,
                processing_time=current_status.processing_duration
            )
        elif status == ProcessingStatus.FAILED:
            self._update_metrics(
                failed_documents=1,
                error_type=error_message
            )
            
        return current_status
        
    def get_status(self, document_id: str) -> Optional[DocumentStatus]:
        """Get the current status of a document"""
        status_data = self.redis_client.get(self._get_status_key(document_id))
        if status_data:
            return DocumentStatus.parse_raw(status_data)
        return None
        
    def get_all_statuses(self) -> List[DocumentStatus]:
        """Get status of all documents"""
        statuses = []
        for key in self.redis_client.scan_iter(f"{self.status_prefix}*"):
            status_data = self.redis_client.get(key)
            if status_data:
                statuses.append(DocumentStatus.parse_raw(status_data))
        return statuses
        
    def get_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics"""
        metrics_data = self.redis_client.get(self.metrics_key)
        if metrics_data:
            return ProcessingMetrics.parse_raw(metrics_data)
        return ProcessingMetrics()
        
    def _get_history(self, document_id: str) -> List[Dict[str, Any]]:
        """Get processing history for a document"""
        history_data = self.redis_client.get(self._get_history_key(document_id))
        if history_data:
            return json.loads(history_data)
        return []
        
    def get_processing_history(
        self,
        document_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered processing history for a document"""
        history = self._get_history(document_id)
        
        if start_time:
            history = [
                entry for entry in history
                if datetime.fromisoformat(entry["timestamp"]) >= start_time
            ]
            
        if end_time:
            history = [
                entry for entry in history
                if datetime.fromisoformat(entry["timestamp"]) <= end_time
            ]
            
        return history
        
    def _update_metrics(
        self,
        total_documents: int = 0,
        processed_documents: int = 0,
        failed_documents: int = 0,
        total_entities: int = 0,
        total_relationships: int = 0,
        entity_types: Optional[Dict[str, int]] = None,
        relationship_types: Optional[Dict[str, int]] = None,
        confidence_scores: Optional[Dict[str, float]] = None,
        processing_time: Optional[float] = None,
        error_type: Optional[str] = None
    ):
        """Update processing metrics"""
        metrics = self.get_metrics()
        
        # Update basic metrics
        metrics.total_documents += total_documents
        metrics.processed_documents += processed_documents
        metrics.failed_documents += failed_documents
        metrics.total_entities += total_entities
        metrics.total_relationships += total_relationships
        
        # Update entity and relationship type counts
        if entity_types:
            for entity_type, count in entity_types.items():
                metrics.entities_by_type[entity_type] = metrics.entities_by_type.get(entity_type, 0) + count
                
        if relationship_types:
            for rel_type, count in relationship_types.items():
                metrics.relationships_by_type[rel_type] = metrics.relationships_by_type.get(rel_type, 0) + count
                
        # Update confidence scores
        if confidence_scores:
            total_confidence = sum(confidence_scores.values())
            count = len(confidence_scores)
            if count > 0:
                metrics.average_confidence = (
                    (metrics.average_confidence * metrics.processed_documents + total_confidence) /
                    (metrics.processed_documents + 1)
                )
                
        # Update processing times
        if processing_time:
            metrics.processing_times.setdefault("all", []).append(processing_time)
            metrics.average_processing_time = sum(metrics.processing_times["all"]) / len(metrics.processing_times["all"])
            metrics.peak_processing_time = max(metrics.processing_times["all"])
            
        # Update error counts
        if error_type:
            metrics.error_counts[error_type] = metrics.error_counts.get(error_type, 0) + 1
            
        # Calculate derived metrics
        if metrics.total_documents > 0:
            metrics.success_rate = metrics.processed_documents / metrics.total_documents
            metrics.average_entities_per_document = metrics.total_entities / metrics.processed_documents
            metrics.average_relationships_per_document = metrics.total_relationships / metrics.processed_documents
            
        # Calculate processing speed
        if metrics.processing_times.get("all"):
            total_time = sum(metrics.processing_times["all"])
            if total_time > 0:
                metrics.processing_speed = (metrics.processed_documents * 3600) / total_time  # docs per hour
                
        metrics.last_updated = datetime.utcnow()
        
        # Store in Redis
        self.redis_client.set(
            self.metrics_key,
            metrics.json(),
            ex=86400
        )
        
    def clear_status(self, document_id: str) -> bool:
        """Clear status for a document"""
        return bool(self.redis_client.delete(self._get_status_key(document_id)))
        
    def clear_all_statuses(self) -> int:
        """Clear all document statuses"""
        count = 0
        for key in self.redis_client.scan_iter(f"{self.status_prefix}*"):
            count += self.redis_client.delete(key)
        return count
        
    def get_performance_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate a performance report for the specified time period"""
        statuses = self.get_all_statuses()
        
        if start_time:
            statuses = [
                status for status in statuses
                if status.start_time >= start_time
            ]
            
        if end_time:
            statuses = [
                status for status in statuses
                if status.start_time <= end_time
            ]
            
        completed_statuses = [
            status for status in statuses
            if status.status == ProcessingStatus.COMPLETED
        ]
        
        failed_statuses = [
            status for status in statuses
            if status.status == ProcessingStatus.FAILED
        ]
        
        total_time = sum(
            status.processing_duration or 0
            for status in completed_statuses
        )
        
        return {
            "period": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None
            },
            "total_documents": len(statuses),
            "completed_documents": len(completed_statuses),
            "failed_documents": len(failed_statuses),
            "success_rate": len(completed_statuses) / len(statuses) if statuses else 0,
            "average_processing_time": total_time / len(completed_statuses) if completed_statuses else 0,
            "total_processing_time": total_time,
            "documents_per_hour": (len(completed_statuses) * 3600) / total_time if total_time > 0 else 0,
            "error_distribution": {
                error: len([s for s in failed_statuses if s.error_message == error])
                for error in set(s.error_message for s in failed_statuses if s.error_message)
            },
            "stage_distribution": {
                stage: len([s for s in statuses if s.current_stage == stage])
                for stage in ProcessingStage
            }
        } 