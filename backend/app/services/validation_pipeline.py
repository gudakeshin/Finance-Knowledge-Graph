from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
import logging
from .validation_service import ValidationService, ValidationReport
from .quality_control import QualityControlService, QualityMetricType
from ..models.graph_models import Entity, Relationship, EntityType, RelationshipType
from enum import Enum
import time
import re
from ..models.validation_models import ValidationRule
from ..models.status_models import ValidationStatus, CorrectionStatus
from ..models.correction_models import CorrectionStrategyEnum
from ..models.batch_models import BatchStatus, BatchSummary
from ..models.history_models import ValidationHistory, CorrectionHistory, BatchHistory
from ..models.summary_models import ValidationSummary, CorrectionSummary, BatchSummary
from ..models.visualization_models import (
    TimeSeriesRequest, TimeSeriesResponse,
    QualityMetricsRequest, QualityMetricsResponse,
    HeatmapRequest, HeatmapResponse,
    NetworkGraphRequest, NetworkGraphResponse,
    DashboardRequest, DashboardResponse
)
from ..models.financial_domain import FinancialDomain

logger = logging.getLogger(__name__)

class FinancialDomain(str, Enum):
    BANKING = "banking"
    INVESTMENT = "investment"
    INSURANCE = "insurance"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    FINTECH = "fintech"
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    WEALTH_MANAGEMENT = "wealth_management"
    HEDGE_FUND = "hedge_fund"
    PRIVATE_EQUITY = "private_equity"
    VENTURE_CAPITAL = "venture_capital"
    ASSET_MANAGEMENT = "asset_management"
    MARKET_MAKING = "market_making"
    QUANTITATIVE_TRADING = "quantitative_trading"

class BatchValidationResult:
    """Result of batch validation operation"""
    total_entities: int
    processed_entities: int
    validation_reports: List[ValidationReport]
    quality_metrics: List[Dict[str, Any]]
    start_time: datetime
    end_time: datetime
    status: str
    error_count: int
    warning_count: int
    success_count: int
    average_confidence: float
    processing_time: float

class BatchCorrectionResult:
    """Result of batch correction operation"""
    total_entities: int
    processed_entities: int
    corrected_entities: int
    failed_corrections: int
    correction_details: List[Dict[str, Any]]
    start_time: datetime
    end_time: datetime
    status: str
    success_rate: float
    processing_time: float

class ValidationPipeline:
    """Pipeline for validating entities and relationships"""
    
    def __init__(
        self,
        validation_service: ValidationService,
        quality_control: QualityControlService
    ):
        self.validation_service = validation_service
        self.quality_control = quality_control
        self.correction_strategies = self._initialize_correction_strategies()
        
    def _initialize_correction_strategies(self) -> Dict[str, Callable]:
        """Initialize correction strategies for different types of issues."""
        return {
            CorrectionStrategyEnum.ADD: self._add_missing_field,
            CorrectionStrategyEnum.REMOVE: self._remove_invalid_field,
            CorrectionStrategyEnum.UPDATE: self._update_field_value,
            CorrectionStrategyEnum.FORMAT: self._format_field_value,
            CorrectionStrategyEnum.CONVERT: self._convert_field_type,
            CorrectionStrategyEnum.ADJUST: self._adjust_field_value,
            CorrectionStrategyEnum.NORMALIZE: self._normalize_field_value,
            CorrectionStrategyEnum.STANDARDIZE: self._standardize_field_value,
            CorrectionStrategyEnum.VALIDATE: self._validate_field_value,
            CorrectionStrategyEnum.ENRICH: self._enrich_field_value,
            CorrectionStrategyEnum.DEDUPLICATE: self._deduplicate_entities,
            CorrectionStrategyEnum.MERGE: self._merge_entities,
            CorrectionStrategyEnum.SPLIT: self._split_entity,
            CorrectionStrategyEnum.TRANSFORM: self._transform_field_value,
            CorrectionStrategyEnum.CALCULATE: self._calculate_field_value,
            CorrectionStrategyEnum.INFER: self._infer_field_value,
            CorrectionStrategyEnum.VALIDATE_FORMAT: self._validate_field_format,
            CorrectionStrategyEnum.VALIDATE_RANGE: self._validate_field_range,
            CorrectionStrategyEnum.VALIDATE_PATTERN: self._validate_field_pattern,
            CorrectionStrategyEnum.VALIDATE_RELATIONSHIP: self._validate_relationship,
            CorrectionStrategyEnum.VALIDATE_CONSISTENCY: self._validate_consistency,
            CorrectionStrategyEnum.VALIDATE_COMPLETENESS: self._validate_completeness,
            CorrectionStrategyEnum.VALIDATE_ACCURACY: self._validate_accuracy,
            CorrectionStrategyEnum.VALIDATE_TIMELINESS: self._validate_timeliness,
            CorrectionStrategyEnum.VALIDATE_UNIQUENESS: self._validate_uniqueness,
            CorrectionStrategyEnum.VALIDATE_INTEGRITY: self._validate_integrity,
            CorrectionStrategyEnum.VALIDATE_CONFORMITY: self._validate_conformity,
            CorrectionStrategyEnum.VALIDATE_BUSINESS_RULES: self._validate_business_rules
        }

    async def _add_missing_field(self, entity: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """Add a missing field to an entity."""
        if field not in entity:
            entity[field] = value
        return entity

    async def _remove_invalid_field(self, entity: Dict[str, Any], field: str) -> Dict[str, Any]:
        """Remove an invalid field from an entity."""
        if field in entity:
            del entity[field]
        return entity

    async def _update_field_value(self, entity: Dict[str, Any], field: str, value: Any) -> Dict[str, Any]:
        """Update a field value in an entity."""
        entity[field] = value
        return entity

    async def _format_field_value(self, entity: Dict[str, Any], field: str, format_spec: str) -> Dict[str, Any]:
        """Format a field value according to a specified format."""
        if field in entity:
            try:
                entity[field] = format(entity[field], format_spec)
            except (ValueError, TypeError):
                pass
        return entity

    async def _convert_field_type(self, entity: Dict[str, Any], field: str, target_type: type) -> Dict[str, Any]:
        """Convert a field value to a specified type."""
        if field in entity:
            try:
                entity[field] = target_type(entity[field])
            except (ValueError, TypeError):
                pass
        return entity

    async def _adjust_field_value(self, entity: Dict[str, Any], field: str, adjustment: Any) -> Dict[str, Any]:
        """Adjust a field value by a specified amount."""
        if field in entity and isinstance(entity[field], (int, float)):
            try:
                entity[field] += adjustment
            except (ValueError, TypeError):
                pass
        return entity

    async def _normalize_field_value(self, entity: Dict[str, Any], field: str) -> Dict[str, Any]:
        """Normalize a field value (e.g., trim whitespace, convert to lowercase)."""
        if field in entity and isinstance(entity[field], str):
            entity[field] = entity[field].strip().lower()
        return entity

    async def _standardize_field_value(self, entity: Dict[str, Any], field: str, standard: Dict[str, str]) -> Dict[str, Any]:
        """Standardize a field value according to a mapping of values."""
        if field in entity and entity[field] in standard:
            entity[field] = standard[entity[field]]
        return entity

    async def _validate_field_value(self, entity: Dict[str, Any], field: str, validation_func: Callable) -> Dict[str, Any]:
        """Validate a field value using a custom validation function."""
        if field in entity:
            try:
                if not validation_func(entity[field]):
                    del entity[field]
            except Exception:
                del entity[field]
        return entity

    async def _enrich_field_value(self, entity: Dict[str, Any], field: str, enrichment_func: Callable) -> Dict[str, Any]:
        """Enrich a field value using a custom enrichment function."""
        if field in entity:
            try:
                entity[field] = enrichment_func(entity[field])
            except Exception:
                pass
        return entity

    async def _deduplicate_entities(self, entities: List[Dict[str, Any]], key_fields: List[str]) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on specified key fields."""
        seen = set()
        unique_entities = []
        for entity in entities:
            key = tuple(entity.get(field) for field in key_fields)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        return unique_entities

    async def _merge_entities(self, entities: List[Dict[str, Any]], merge_func: Callable) -> List[Dict[str, Any]]:
        """Merge entities using a custom merge function."""
        return merge_func(entities)

    async def _split_entity(self, entity: Dict[str, Any], split_func: Callable) -> List[Dict[str, Any]]:
        """Split an entity into multiple entities using a custom split function."""
        return split_func(entity)

    async def _transform_field_value(self, entity: Dict[str, Any], field: str, transform_func: Callable) -> Dict[str, Any]:
        """Transform a field value using a custom transformation function."""
        if field in entity:
            try:
                entity[field] = transform_func(entity[field])
            except Exception:
                pass
        return entity

    async def _calculate_field_value(self, entity: Dict[str, Any], field: str, calculation_func: Callable) -> Dict[str, Any]:
        """Calculate a field value using a custom calculation function."""
        try:
            entity[field] = calculation_func(entity)
        except Exception:
            pass
        return entity

    async def _infer_field_value(self, entity: Dict[str, Any], field: str, inference_func: Callable) -> Dict[str, Any]:
        """Infer a field value using a custom inference function."""
        if field not in entity:
            try:
                entity[field] = inference_func(entity)
            except Exception:
                pass
        return entity

    async def _validate_field_format(self, entity: Dict[str, Any], field: str, format_pattern: str) -> Dict[str, Any]:
        """Validate a field value against a format pattern."""
        if field in entity:
            try:
                if not re.match(format_pattern, str(entity[field])):
                    del entity[field]
            except Exception:
                del entity[field]
        return entity

    async def _validate_field_range(self, entity: Dict[str, Any], field: str, min_value: Any, max_value: Any) -> Dict[str, Any]:
        """Validate a field value against a range."""
        if field in entity:
            try:
                if not (min_value <= entity[field] <= max_value):
                    del entity[field]
            except Exception:
                del entity[field]
        return entity

    async def _validate_field_pattern(self, entity: Dict[str, Any], field: str, pattern: str) -> Dict[str, Any]:
        """Validate a field value against a regex pattern."""
        if field in entity:
            try:
                if not re.match(pattern, str(entity[field])):
                    del entity[field]
            except Exception:
                del entity[field]
        return entity

    async def _validate_relationship(self, entity: Dict[str, Any], relationship: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a relationship between entities."""
        # Implementation depends on specific relationship validation rules
        return entity

    async def _validate_consistency(self, entity: Dict[str, Any], consistency_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate consistency between fields."""
        for rule in consistency_rules:
            fields = rule.get("fields", [])
            if all(field in entity for field in fields):
                try:
                    if not rule["validation_func"]([entity[field] for field in fields]):
                        for field in fields:
                            del entity[field]
                except Exception:
                    for field in fields:
                        del entity[field]
        return entity

    async def _validate_completeness(self, entity: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Validate completeness of required fields."""
        for field in required_fields:
            if field not in entity or entity[field] is None:
                return None
        return entity

    async def _validate_accuracy(self, entity: Dict[str, Any], accuracy_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate accuracy of field values."""
        for rule in accuracy_rules:
            field = rule.get("field")
            if field in entity:
                try:
                    if not rule["validation_func"](entity[field]):
                        del entity[field]
                except Exception:
                    del entity[field]
        return entity

    async def _validate_timeliness(self, entity: Dict[str, Any], timeliness_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate timeliness of field values."""
        for rule in timeliness_rules:
            field = rule.get("field")
            if field in entity:
                try:
                    if not rule["validation_func"](entity[field]):
                        del entity[field]
                except Exception:
                    del entity[field]
        return entity

    async def _validate_uniqueness(self, entity: Dict[str, Any], unique_fields: List[str]) -> Dict[str, Any]:
        """Validate uniqueness of field values."""
        # Implementation depends on the context of uniqueness validation
        return entity

    async def _validate_integrity(self, entity: Dict[str, Any], integrity_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data integrity."""
        for rule in integrity_rules:
            try:
                if not rule["validation_func"](entity):
                    return None
            except Exception:
                return None
        return entity

    async def _validate_conformity(self, entity: Dict[str, Any], conformity_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate conformity to standards."""
        for rule in conformity_rules:
            field = rule.get("field")
            if field in entity:
                try:
                    if not rule["validation_func"](entity[field]):
                        del entity[field]
                except Exception:
                    del entity[field]
        return entity

    async def _validate_business_rules(self, entity: Dict[str, Any], business_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate business rules."""
        for rule in business_rules:
            try:
                if not rule["validation_func"](entity):
                    return None
            except Exception:
                return None
        return entity

    async def apply_correction(self, entity: Dict[str, Any], correction: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a correction to an entity."""
        strategy = correction.get("strategy")
        if strategy in self.correction_strategies:
            try:
                return await self.correction_strategies[strategy](entity, **correction.get("parameters", {}))
            except Exception as e:
                logger.error(f"Error applying correction {strategy}: {str(e)}")
        return entity

    async def validate_entity_pipeline(
        self,
        entity: Entity,
        update_quality: bool = True
    ) -> Tuple[ValidationReport, Dict[str, Any]]:
        """
        Run the complete validation pipeline for an entity
        
        Args:
            entity: Entity to validate
            update_quality: Whether to update quality metrics
            
        Returns:
            Tuple of (validation report, quality metrics)
        """
        try:
            # Run validation rules
            validation_report = self.validation_service.validate_entity(entity)
            
            if update_quality:
                # Calculate quality metrics
                quality_metrics = self._calculate_entity_quality_metrics(
                    entity,
                    validation_report
                )
                
                # Update quality control metrics
                for metric_type, (value, threshold, details) in quality_metrics.items():
                    self.quality_control.update_metric(
                        metric_type=metric_type,
                        value=value,
                        threshold=threshold,
                        details=details,
                        entity_type=entity.type
                    )
                    
                return validation_report, quality_metrics
                
            return validation_report, {}
            
        except Exception as e:
            logger.error(f"Error in entity validation pipeline: {str(e)}")
            raise
            
    def validate_relationship_pipeline(
        self,
        relationship: Relationship,
        source_entity: Optional[Entity] = None,
        target_entity: Optional[Entity] = None,
        update_quality: bool = True
    ) -> Tuple[ValidationReport, Dict[str, Any]]:
        """
        Run the complete validation pipeline for a relationship
        
        Args:
            relationship: Relationship to validate
            source_entity: Optional source entity
            target_entity: Optional target entity
            update_quality: Whether to update quality metrics
            
        Returns:
            Tuple of (validation report, quality metrics)
        """
        try:
            # Run validation rules
            validation_report = self.validation_service.validate_relationship(relationship)
            
            if update_quality:
                # Calculate quality metrics
                quality_metrics = self._calculate_relationship_quality_metrics(
                    relationship,
                    validation_report,
                    source_entity,
                    target_entity
                )
                
                # Update quality control metrics
                for metric_type, (value, threshold, details) in quality_metrics.items():
                    self.quality_control.update_metric(
                        metric_type=metric_type,
                        value=value,
                        threshold=threshold,
                        details=details
                    )
                    
                return validation_report, quality_metrics
                
            return validation_report, {}
            
        except Exception as e:
            logger.error(f"Error in relationship validation pipeline: {str(e)}")
            raise
            
    def _calculate_entity_quality_metrics(
        self,
        entity: Entity,
        validation_report: ValidationReport
    ) -> Dict[QualityMetricType, Tuple[float, float, Dict[str, Any]]]:
        """Calculate quality metrics for an entity"""
        metrics = {}
        
        # Completeness
        required_props = len([
            rule for rule in self.validation_service.entity_rules.get(entity.type, [])
            for prop in rule.required_properties
        ])
        actual_props = len([
            prop for prop in entity.properties.keys()
            if any(prop in rule.required_properties
                  for rule in self.validation_service.entity_rules.get(entity.type, []))
        ])
        completeness = actual_props / required_props if required_props > 0 else 1.0
        
        metrics[QualityMetricType.COMPLETENESS] = (
            completeness,
            0.8,  # 80% threshold
            {
                "required_properties": required_props,
                "actual_properties": actual_props,
                "missing_properties": [
                    prop for rule in self.validation_service.entity_rules.get(entity.type, [])
                    for prop in rule.required_properties
                    if prop not in entity.properties
                ]
            }
        )
        
        # Consistency
        consistency_errors = len([
            result for result in validation_report.results
            if result.level == "error" and "pattern" in result.details
        ])
        consistency = 1.0 - (consistency_errors / len(validation_report.results)) if validation_report.results else 1.0
        
        metrics[QualityMetricType.CONSISTENCY] = (
            consistency,
            0.9,  # 90% threshold
            {
                "consistency_errors": consistency_errors,
                "total_checks": len(validation_report.results)
            }
        )
        
        # Validity
        validity_errors = len([
            result for result in validation_report.results
            if result.level == "error" and "range" in result.details
        ])
        validity = 1.0 - (validity_errors / len(validation_report.results)) if validation_report.results else 1.0
        
        metrics[QualityMetricType.VALIDITY] = (
            validity,
            0.9,  # 90% threshold
            {
                "validity_errors": validity_errors,
                "total_checks": len(validation_report.results)
            }
        )
        
        return metrics
        
    def _calculate_relationship_quality_metrics(
        self,
        relationship: Relationship,
        validation_report: ValidationReport,
        source_entity: Optional[Entity] = None,
        target_entity: Optional[Entity] = None
    ) -> Dict[QualityMetricType, Tuple[float, float, Dict[str, Any]]]:
        """Calculate quality metrics for a relationship"""
        metrics = {}
        
        # Completeness
        required_props = len([
            rule for rule in self.validation_service.relationship_rules.get(relationship.type, [])
            for prop in rule.required_properties
        ])
        actual_props = len([
            prop for prop in relationship.properties.keys()
            if any(prop in rule.required_properties
                  for rule in self.validation_service.relationship_rules.get(relationship.type, []))
        ])
        completeness = actual_props / required_props if required_props > 0 else 1.0
        
        metrics[QualityMetricType.COMPLETENESS] = (
            completeness,
            0.8,  # 80% threshold
            {
                "required_properties": required_props,
                "actual_properties": actual_props,
                "missing_properties": [
                    prop for rule in self.validation_service.relationship_rules.get(relationship.type, [])
                    for prop in rule.required_properties
                    if prop not in relationship.properties
                ]
            }
        )
        
        # Consistency
        consistency_errors = len([
            result for result in validation_report.results
            if result.level == "error" and "pattern" in result.details
        ])
        consistency = 1.0 - (consistency_errors / len(validation_report.results)) if validation_report.results else 1.0
        
        metrics[QualityMetricType.CONSISTENCY] = (
            consistency,
            0.9,  # 90% threshold
            {
                "consistency_errors": consistency_errors,
                "total_checks": len(validation_report.results)
            }
        )
        
        # Entity type consistency
        if source_entity and target_entity:
            type_errors = 0
            for rule in self.validation_service.relationship_rules.get(relationship.type, []):
                if source_entity.type not in rule.source_types:
                    type_errors += 1
                if target_entity.type not in rule.target_types:
                    type_errors += 1
                    
            type_consistency = 1.0 - (type_errors / 2) if type_errors > 0 else 1.0
            
            metrics[QualityMetricType.VALIDITY] = (
                type_consistency,
                1.0,  # 100% threshold
                {
                    "type_errors": type_errors,
                    "source_type": source_entity.type.value,
                    "target_type": target_entity.type.value
                }
            )
            
        return metrics
        
    def get_validation_summary(
        self,
        entity_type: Optional[EntityType] = None
    ) -> Dict[str, Any]:
        """Get a summary of validation and quality metrics"""
        try:
            # Get quality report
            quality_report = self.quality_control.get_quality_report(entity_type)
            
            # Get validation rules
            validation_rules = self.validation_service.get_validation_rules()
            
            return {
                "quality_metrics": quality_report,
                "validation_rules": {
                    "entity_rules": len(validation_rules["entity_rules"]),
                    "relationship_rules": len(validation_rules["relationship_rules"])
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting validation summary: {str(e)}")
            return {}

    async def validate_entity_batch(
        self,
        entities: List[Entity],
        domain: Optional[FinancialDomain] = None,
        update_quality_metrics: bool = True,
        batch_size: int = 100
    ) -> BatchValidationResult:
        """Validate a batch of entities"""
        start_time = datetime.utcnow()
        total_entities = len(entities)
        processed_entities = 0
        validation_reports = []
        quality_metrics = []
        error_count = 0
        warning_count = 0
        success_count = 0
        confidence_scores = []

        try:
            # Process entities in batches
            for i in range(0, total_entities, batch_size):
                batch = entities[i:i + batch_size]
                
                # Validate each entity in the batch
                for entity in batch:
                    try:
                        if domain:
                            report = self.validation_service.validate_financial_entity(entity, domain)
                        else:
                            report = self.validation_service.validate_entity(entity)
                        
                        validation_reports.append(report)
                        confidence_scores.append(report.confidence_score)
                        
                        # Update quality metrics if requested
                        if update_quality_metrics:
                            metrics = self._calculate_entity_quality_metrics(entity, report)
                            self.quality_control.update_quality_metrics(metrics)
                            quality_metrics.extend(metrics)
                        
                        # Update counters
                        if report.has_errors():
                            error_count += 1
                        elif report.has_warnings():
                            warning_count += 1
                        else:
                            success_count += 1
                            
                        processed_entities += 1
                        
                    except Exception as e:
                        logger.error(f"Error validating entity {entity.id}: {str(e)}")
                        error_count += 1
                        processed_entities += 1

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Calculate average confidence score
            average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return BatchValidationResult(
                total_entities=total_entities,
                processed_entities=processed_entities,
                validation_reports=validation_reports,
                quality_metrics=quality_metrics,
                start_time=start_time,
                end_time=end_time,
                status="completed",
                error_count=error_count,
                warning_count=warning_count,
                success_count=success_count,
                average_confidence=average_confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in batch validation: {str(e)}")
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            return BatchValidationResult(
                total_entities=total_entities,
                processed_entities=processed_entities,
                validation_reports=validation_reports,
                quality_metrics=quality_metrics,
                start_time=start_time,
                end_time=end_time,
                status="failed",
                error_count=error_count,
                warning_count=warning_count,
                success_count=success_count,
                average_confidence=0.0,
                processing_time=processing_time
            )

    async def correct_entity_batch(
        self,
        entities: List[Entity],
        validation_reports: List[ValidationReport],
        auto_apply: bool = False,
        batch_size: int = 100
    ) -> BatchCorrectionResult:
        """Apply corrections to a batch of entities"""
        start_time = datetime.utcnow()
        total_entities = len(entities)
        processed_entities = 0
        corrected_entities = 0
        failed_corrections = 0
        correction_details = []

        try:
            # Process entities in batches
            for i in range(0, total_entities, batch_size):
                batch = entities[i:i + batch_size]
                batch_reports = validation_reports[i:i + batch_size]
                
                # Apply corrections to each entity in the batch
                for entity, report in zip(batch, batch_reports):
                    try:
                        entity_corrections = []
                        success = True
                        
                        # Apply each correction
                        for result in report.results:
                            if result.suggested_corrections:
                                for correction in result.suggested_corrections:
                                    try:
                                        if auto_apply:
                                            self._apply_correction(entity, correction)
                                        entity_corrections.append({
                                            "rule": result.rule_name,
                                            "field": correction["field"],
                                            "action": correction["action"],
                                            "description": correction["description"],
                                            "status": "applied" if auto_apply else "suggested"
                                        })
                                    except Exception as e:
                                        logger.error(f"Error applying correction to entity {entity.id}: {str(e)}")
                                        success = False
                                        entity_corrections.append({
                                            "rule": result.rule_name,
                                            "field": correction["field"],
                                            "action": correction["action"],
                                            "description": correction["description"],
                                            "status": "failed",
                                            "error": str(e)
                                        })
                        
                        correction_details.append({
                            "entity_id": entity.id,
                            "corrections": entity_corrections,
                            "success": success
                        })
                        
                        if success:
                            corrected_entities += 1
                        else:
                            failed_corrections += 1
                            
                        processed_entities += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing entity {entity.id}: {str(e)}")
                        failed_corrections += 1
                        processed_entities += 1

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Calculate success rate
            success_rate = (corrected_entities / total_entities) * 100 if total_entities > 0 else 0.0
            
            return BatchCorrectionResult(
                total_entities=total_entities,
                processed_entities=processed_entities,
                corrected_entities=corrected_entities,
                failed_corrections=failed_corrections,
                correction_details=correction_details,
                start_time=start_time,
                end_time=end_time,
                status="completed",
                success_rate=success_rate,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in batch correction: {str(e)}")
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            return BatchCorrectionResult(
                total_entities=total_entities,
                processed_entities=processed_entities,
                corrected_entities=corrected_entities,
                failed_corrections=failed_corrections,
                correction_details=correction_details,
                start_time=start_time,
                end_time=end_time,
                status="failed",
                success_rate=0.0,
                processing_time=processing_time
            )

    def _apply_correction(self, entity: Entity, correction: Dict[str, Any]):
        """Apply a single correction to an entity"""
        field = correction["field"]
        action = correction["action"]
        
        if action == "add":
            if field not in entity.properties:
                entity.properties[field] = None
        elif action == "remove":
            if field in entity.properties:
                del entity.properties[field]
        elif action == "update":
            if field in entity.properties:
                # Apply the correction value if provided
                if "value" in correction:
                    entity.properties[field] = correction["value"]
        elif action == "format":
            if field in entity.properties:
                # Apply formatting based on the field type
                value = entity.properties[field]
                if isinstance(value, str):
                    # Apply string formatting
                    if "format" in correction:
                        entity.properties[field] = correction["format"].format(value)
                elif isinstance(value, (int, float)):
                    # Apply numeric formatting
                    if "format" in correction:
                        entity.properties[field] = float(correction["format"].format(value))
        elif action == "convert":
            if field in entity.properties:
                # Convert value to the specified type
                value = entity.properties[field]
                if "type" in correction:
                    target_type = correction["type"]
                    if target_type == "int":
                        entity.properties[field] = int(value)
                    elif target_type == "float":
                        entity.properties[field] = float(value)
                    elif target_type == "str":
                        entity.properties[field] = str(value)
                    elif target_type == "bool":
                        entity.properties[field] = bool(value)
                    elif target_type == "date":
                        entity.properties[field] = datetime.fromisoformat(value)
        elif action == "adjust":
            if field in entity.properties:
                # Adjust numeric value within range
                value = float(entity.properties[field])
                if "min" in correction and "max" in correction:
                    min_val = float(correction["min"])
                    max_val = float(correction["max"])
                    entity.properties[field] = max(min_val, min(value, max_val)) 