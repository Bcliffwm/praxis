"""
Core package for Research GraphRAG.

Contains configuration, database clients, and data models.
"""

from .config import ConfigManager, Config
from .database import Neo4jClient
from .models import (
    NetworkAnalysisResult, NetworkAnalysisConfig, CommunityInfo,
    QueryResult, MatchPattern, Aggregation, OrderBy, Filter, CypherQueryPlan
)

__all__ = [
    "ConfigManager",
    "Config", 
    "Neo4jClient",
    "NetworkAnalysisResult",
    "NetworkAnalysisConfig",
    "CommunityInfo",
    "QueryResult",
    "MatchPattern",
    "Aggregation", 
    "OrderBy",
    "Filter",
    "CypherQueryPlan"
]