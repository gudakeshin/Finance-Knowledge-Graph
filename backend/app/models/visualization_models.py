from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class VisualizationRequest(BaseModel):
    data: Dict[str, Any]
    chart_type: str
    options: Optional[Dict[str, Any]] = None

class VisualizationResponse(BaseModel):
    chart_url: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DashboardRequest(BaseModel):
    filters: Optional[Dict[str, Any]] = None
    layout: Optional[str] = None

class DashboardResponse(BaseModel):
    dashboard_id: str
    widgets: List[Dict[str, Any]]
    layout: Optional[str] = None
    error: Optional[str] = None

class TimeSeriesRequest(BaseModel):
    series_data: Dict[str, Any]
    time_column: str
    value_column: str
    options: Optional[Dict[str, Any]] = None

class TimeSeriesResponse(BaseModel):
    chart_url: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class QualityMetricsRequest(BaseModel):
    metrics: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None

class QualityMetricsResponse(BaseModel):
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HeatmapRequest(BaseModel):
    data: Dict[str, Any]
    x_axis: str
    y_axis: str
    value_field: str
    options: Optional[Dict[str, Any]] = None

class HeatmapResponse(BaseModel):
    chart_url: Optional[str] = None
    chart_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class NetworkGraphRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None

class NetworkGraphResponse(BaseModel):
    graph_url: Optional[str] = None
    graph_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 