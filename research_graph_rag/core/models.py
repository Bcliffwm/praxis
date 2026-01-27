"""
Data models for Research GraphRAG package.

Contains Pydantic models and data classes for structured data handling.
"""

from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass
from pydantic import BaseModel, Field


# Type definitions
AuthorLabel = Literal["Author"]
TopicLabel = Literal["Topic"] 
WorkLabel = Literal["Work"]
RelationshipType = Literal["WORK_AUTHORED_BY", "WORK_HAS_TOPIC", "RELATED_TO"]
Direction = Literal["OUT", "IN", "BOTH"]


class MatchPattern(BaseModel):
    """Match pattern for Cypher queries."""
    start_label: str
    relationship: RelationshipType
    end_label: str
    direction: Direction = "OUT"


class Aggregation(BaseModel):
    """Aggregation specification for Cypher queries."""
    function: Literal["count", "sum", "avg", "max", "min"]
    variable: str
    alias: str


class OrderBy(BaseModel):
    """Order by specification for Cypher queries."""
    field: str
    direction: Literal["ASC", "DESC"] = "DESC"


class Filter(BaseModel):
    """Filter specification for Cypher queries."""
    field: str
    op: Literal["=", ">", "<", ">=", "<=", "CONTAINS", "STARTS WITH", "ENDS WITH"]
    value: Any


class CypherQueryPlan(BaseModel):
    """Complete Cypher query plan specification."""
    match: MatchPattern
    aggregations: List[Aggregation] = Field(default_factory=list)
    return_fields: List[str]
    filters: List[Filter] = Field(default_factory=list)
    order_by: Optional[OrderBy] = None
    limit: Optional[int] = None


@dataclass
class NetworkAnalysisResult:
    """Container for network analysis results with metrics."""
    
    work_id: str
    title: str
    metrics: Dict[str, float]
    confidence_score: Optional[float] = None
    
    def __post_init__(self):
        """Calculate confidence score after initialization."""
        if self.confidence_score is None:
            self.confidence_score = self._calculate_confidence()
    
    def _calculate_confidence(self) -> float:
        """Calculate composite confidence score from multiple metrics."""
        weights = {
            'degree_centrality': 0.2,
            'betweenness_centrality': 0.3,
            'closeness_centrality': 0.2,
            'pagerank_score': 0.3,
            'same_community': 0.5  # Bonus for same community
        }
        
        score = 0.0
        total_weight = 0.0
        
        for metric, value in self.metrics.items():
            if metric in weights and value is not None:
                score += weights[metric] * float(value)
                total_weight += weights[metric]
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'work_id': self.work_id,
            'title': self.title,
            'metrics': self.metrics,
            'confidence_score': self.confidence_score
        }
    
    def get_metric(self, metric_name: str, default: float = 0.0) -> float:
        """Get a specific metric value."""
        return self.metrics.get(metric_name, default)
    
    def has_metric(self, metric_name: str) -> bool:
        """Check if a specific metric exists."""
        return metric_name in self.metrics
    
    def get_confidence_level(self) -> str:
        """Get human-readable confidence level."""
        if self.confidence_score >= 0.8:
            return "Very High"
        elif self.confidence_score >= 0.6:
            return "High"
        elif self.confidence_score >= 0.4:
            return "Moderate"
        elif self.confidence_score >= 0.2:
            return "Low"
        else:
            return "Very Low"


class QueryResult(BaseModel):
    """Standard query result container."""
    
    query_type: str
    success: bool
    row_count: int = 0
    records: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
    
    def is_successful(self) -> bool:
        """Check if query was successful."""
        return self.success and not self.error_message
    
    def has_results(self) -> bool:
        """Check if query returned results."""
        return self.row_count > 0 and len(self.records) > 0
    
    def get_first_record(self) -> Optional[Dict[str, Any]]:
        """Get the first record if available."""
        return self.records[0] if self.records else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query_type': self.query_type,
            'success': self.success,
            'row_count': self.row_count,
            'records': self.records,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'metadata': self.metadata
        }


class NetworkAnalysisConfig(BaseModel):
    """Configuration for network analysis operations."""
    
    graph_name: str = "research_network"
    analysis_types: List[str] = Field(default_factory=lambda: ["comprehensive"])
    limit: int = 20
    min_confidence: float = 0.0
    include_metrics: List[str] = Field(default_factory=lambda: [
        "degree_centrality", "betweenness_centrality", 
        "closeness_centrality", "pagerank_score"
    ])
    community_detection: bool = True
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
    
    def validate_analysis_types(self) -> List[str]:
        """Validate and return supported analysis types."""
        supported_types = [
            "comprehensive", "community", "centrality", 
            "shortest_path", "similarity"
        ]
        return [t for t in self.analysis_types if t in supported_types]


class CommunityInfo(BaseModel):
    """Information about a detected community."""
    
    community_id: int
    size: int
    works: List[Dict[str, str]]
    total_works: int
    avg_centrality: Optional[float] = None
    top_work: Optional[Dict[str, Any]] = None
    
    def get_density(self) -> float:
        """Calculate community density (works shown / total works)."""
        return len(self.works) / self.total_works if self.total_works > 0 else 0.0
    
    def is_large_community(self, threshold: int = 5) -> bool:
        """Check if this is a large community."""
        return self.size >= threshold