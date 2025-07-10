from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum
from pydantic import BaseModel, Field
from collections import defaultdict
import redis
import json
import numpy as np
from ..models.graph_models import EntityType, RelationshipType

logger = logging.getLogger(__name__)

class QualityMetricType(str, Enum):
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    RELIABILITY = "reliability"
    INTEGRITY = "integrity"
    CONFORMITY = "conformity"
    UNIQUENESS = "uniqueness"
    BUSINESS_RULES = "business_rules"

class QualityMetric(BaseModel):
    type: QualityMetricType
    value: float
    threshold: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    affected_entities: Optional[List[str]] = None
    affected_relationships: Optional[List[str]] = None
    validation_context: Optional[Dict[str, Any]] = None

class QualityScore(BaseModel):
    score: float
    metrics: Dict[QualityMetricType, QualityMetric]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
    entity_type: Optional[EntityType] = None
    relationship_type: Optional[RelationshipType] = None
    validation_context: Optional[Dict[str, Any]] = None

class QualityControlService:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.metric_weights = {
            QualityMetricType.COMPLETENESS: 0.2,
            QualityMetricType.CONSISTENCY: 0.15,
            QualityMetricType.ACCURACY: 0.15,
            QualityMetricType.TIMELINESS: 0.1,
            QualityMetricType.VALIDITY: 0.1,
            QualityMetricType.RELIABILITY: 0.1,
            QualityMetricType.INTEGRITY: 0.05,
            QualityMetricType.CONFORMITY: 0.05,
            QualityMetricType.UNIQUENESS: 0.05,
            QualityMetricType.BUSINESS_RULES: 0.05
        }

    def _generate_metric_key(self, metric_type: QualityMetricType, entity_type: Optional[EntityType] = None) -> str:
        if entity_type:
            return f"quality:metric:{metric_type}:{entity_type}"
        return f"quality:metric:{metric_type}"

    def _generate_score_key(self, entity_type: Optional[EntityType] = None) -> str:
        if entity_type:
            return f"quality:score:{entity_type}"
        return "quality:score:overall"

    def update_quality_metric(self, metric: QualityMetric, entity_type: Optional[EntityType] = None) -> bool:
        try:
            key = self._generate_metric_key(metric.type, entity_type)
            self.redis.set(key, metric.json())
            return True
        except Exception as e:
            logger.error(f"Error updating quality metric: {str(e)}")
            return False

    def get_quality_metric(self, metric_type: QualityMetricType, entity_type: Optional[EntityType] = None) -> Optional[QualityMetric]:
        try:
            key = self._generate_metric_key(metric_type, entity_type)
            data = self.redis.get(key)
            if data:
                return QualityMetric.parse_raw(data)
            return None
        except Exception as e:
            logger.error(f"Error getting quality metric: {str(e)}")
            return None

    def get_all_metrics(self, entity_type: Optional[EntityType] = None) -> Dict[QualityMetricType, QualityMetric]:
        metrics = {}
        for metric_type in QualityMetricType:
            metric = self.get_quality_metric(metric_type, entity_type)
            if metric:
                metrics[metric_type] = metric
        return metrics

    def calculate_quality_score(self, entity_type: Optional[EntityType] = None) -> QualityScore:
        metrics = self.get_all_metrics(entity_type)
        if not metrics:
            return QualityScore(score=0.0, metrics={})

        weighted_sum = 0.0
        total_weight = 0.0

        for metric_type, metric in metrics.items():
            weight = self.metric_weights.get(metric_type, 0.0)
            weighted_sum += metric.value * weight
            total_weight += weight

        score = weighted_sum / total_weight if total_weight > 0 else 0.0

        return QualityScore(
            score=score,
            metrics=metrics,
            entity_type=entity_type
        )

    def get_quality_report(self, entity_type: Optional[EntityType] = None) -> Dict[str, Any]:
        metrics = self.get_all_metrics(entity_type)
        score = self.calculate_quality_score(entity_type)

        # Calculate trend analysis
        trends = {}
        for metric_type, metric in metrics.items():
            historical_data = self.get_historical_metrics(metric_type, entity_type)
            if historical_data:
                values = [m.value for m in historical_data]
                trends[metric_type] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "trend": np.polyfit(range(len(values)), values, 1)[0],
                    "min": np.min(values),
                    "max": np.max(values)
                }

        # Calculate correlation analysis
        correlations = {}
        metric_values = {m_type: m.value for m_type, m in metrics.items()}
        for m1 in metrics:
            for m2 in metrics:
                if m1 != m2:
                    correlations[f"{m1}_{m2}"] = np.corrcoef(
                        [metric_values[m1]],
                        [metric_values[m2]]
                    )[0, 1]

        # Generate recommendations
        recommendations = []
        for metric_type, metric in metrics.items():
            if metric.value < metric.threshold:
                recommendations.append({
                    "metric": metric_type,
                    "current_value": metric.value,
                    "threshold": metric.threshold,
                    "suggestion": f"Improve {metric_type} quality by addressing issues in {', '.join(metric.affected_entities or [])}"
                })

        return {
            "score": score.dict(),
            "metrics": {k: v.dict() for k, v in metrics.items()},
            "trends": trends,
            "correlations": correlations,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_historical_metrics(self, metric_type: QualityMetricType, entity_type: Optional[EntityType] = None, days: int = 30) -> List[QualityMetric]:
        try:
            key = self._generate_metric_key(metric_type, entity_type)
            data = self.redis.lrange(key, 0, days - 1)
            return [QualityMetric.parse_raw(item) for item in data]
        except Exception as e:
            logger.error(f"Error getting historical metrics: {str(e)}")
            return []

    def get_quality_trends(self, metric_type: QualityMetricType, entity_type: Optional[EntityType] = None, days: int = 30) -> Dict[str, Any]:
        historical_data = self.get_historical_metrics(metric_type, entity_type, days)
        if not historical_data:
            return {}

        values = [m.value for m in historical_data]
        timestamps = [m.timestamp for m in historical_data]

        return {
            "values": values,
            "timestamps": [t.isoformat() for t in timestamps],
            "mean": np.mean(values),
            "std": np.std(values),
            "trend": np.polyfit(range(len(values)), values, 1)[0],
            "min": np.min(values),
            "max": np.max(values),
            "current": values[-1] if values else None
        }

    def get_quality_anomalies(self, metric_type: QualityMetricType, entity_type: Optional[EntityType] = None, days: int = 30) -> List[Dict[str, Any]]:
        historical_data = self.get_historical_metrics(metric_type, entity_type, days)
        if not historical_data:
            return []

        values = [m.value for m in historical_data]
        mean = np.mean(values)
        std = np.std(values)
        threshold = 2  # Number of standard deviations for anomaly detection

        anomalies = []
        for i, (metric, value) in enumerate(zip(historical_data, values)):
            if abs(value - mean) > threshold * std:
                anomalies.append({
                    "timestamp": metric.timestamp.isoformat(),
                    "value": value,
                    "expected_range": (mean - threshold * std, mean + threshold * std),
                    "deviation": value - mean,
                    "details": metric.details
                })

        return anomalies

    def get_quality_benchmarks(self, entity_type: Optional[EntityType] = None) -> Dict[str, Any]:
        metrics = self.get_all_metrics(entity_type)
        if not metrics:
            return {}

        benchmarks = {}
        for metric_type, metric in metrics.items():
            historical_data = self.get_historical_metrics(metric_type, entity_type)
            if historical_data:
                values = [m.value for m in historical_data]
                benchmarks[metric_type] = {
                    "current": metric.value,
                    "average": np.mean(values),
                    "best": np.max(values),
                    "worst": np.min(values),
                    "threshold": metric.threshold,
                    "status": "good" if metric.value >= metric.threshold else "needs_improvement"
                }

        return benchmarks

    def get_quality_impact_analysis(self, entity_type: Optional[EntityType] = None) -> Dict[str, Any]:
        metrics = self.get_all_metrics(entity_type)
        if not metrics:
            return {}

        impact_scores = {}
        for metric_type, metric in metrics.items():
            if metric.value < metric.threshold:
                impact_scores[metric_type] = {
                    "current_value": metric.value,
                    "threshold": metric.threshold,
                    "gap": metric.threshold - metric.value,
                    "impact_score": (metric.threshold - metric.value) * self.metric_weights[metric_type],
                    "affected_entities": metric.affected_entities,
                    "affected_relationships": metric.affected_relationships,
                    "recommendations": self._generate_recommendations(metric_type, metric)
                }

        return {
            "impact_scores": impact_scores,
            "total_impact": sum(score["impact_score"] for score in impact_scores.values()),
            "priority_areas": sorted(impact_scores.items(), key=lambda x: x[1]["impact_score"], reverse=True)
        }

    def _generate_recommendations(self, metric_type: QualityMetricType, metric: QualityMetric) -> List[Dict[str, Any]]:
        recommendations = []
        
        if metric_type == QualityMetricType.COMPLETENESS:
            if metric.affected_entities:
                recommendations.append({
                    "type": "completeness",
                    "action": "add_missing_fields",
                    "entities": metric.affected_entities,
                    "priority": "high" if metric.value < 0.5 else "medium"
                })
        
        elif metric_type == QualityMetricType.CONSISTENCY:
            if metric.details and "inconsistent_fields" in metric.details:
                recommendations.append({
                    "type": "consistency",
                    "action": "standardize_values",
                    "fields": metric.details["inconsistent_fields"],
                    "priority": "high" if metric.value < 0.7 else "medium"
                })
        
        elif metric_type == QualityMetricType.ACCURACY:
            if metric.details and "validation_errors" in metric.details:
                recommendations.append({
                    "type": "accuracy",
                    "action": "correct_errors",
                    "errors": metric.details["validation_errors"],
                    "priority": "high" if metric.value < 0.8 else "medium"
                })
        
        elif metric_type == QualityMetricType.TIMELINESS:
            if metric.details and "stale_data" in metric.details:
                recommendations.append({
                    "type": "timeliness",
                    "action": "update_data",
                    "stale_entities": metric.details["stale_data"],
                    "priority": "high" if metric.value < 0.6 else "medium"
                })
        
        elif metric_type == QualityMetricType.VALIDITY:
            if metric.details and "invalid_values" in metric.details:
                recommendations.append({
                    "type": "validity",
                    "action": "validate_data",
                    "invalid_fields": metric.details["invalid_values"],
                    "priority": "high" if metric.value < 0.9 else "medium"
                })

        return recommendations 