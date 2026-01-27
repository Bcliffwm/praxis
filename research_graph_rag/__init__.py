"""
Research GraphRAG Package

A comprehensive package for research portfolio development using Graph-based
Retrieval-Augmented Generation (GraphRAG) with Neo4j and AWS Bedrock.

Main Components:
- Core agents for research query processing
- Network analysis using Neo4j Graph Data Science
- Configuration management
- Utilities for data processing and validation
"""

__version__ = "1.0.0"
__author__ = "Research GraphRAG Team"
__description__ = "Graph-based research analysis and summarization toolkit"

# Core imports for easy access
from .core.config import ConfigManager
from .agents.base_agent import ResearchQueryAgent
from .agents.relationship_agent import EnhancedResearchQueryAgent
from .agents.network_agent import NetworkAnalysisAgent
from .agents.work_discovery_agent import WorkBasedDiscoveryAgent
from .utils.validators import CypherValidator, EnhancedCypherValidator
from .utils.exceptions import GraphRAGError, ConfigurationError, ValidationError

# Version info
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable"
}

__all__ = [
    # Core classes
    "ConfigManager",
    "ResearchQueryAgent", 
    "EnhancedResearchQueryAgent",
    "NetworkAnalysisAgent",
    "WorkBasedDiscoveryAgent",
    
    # Utilities
    "CypherValidator",
    "EnhancedCypherValidator",
    
    # Exceptions
    "GraphRAGError",
    "ConfigurationError", 
    "ValidationError",
    
    # Version
    "__version__",
    "VERSION_INFO"
]