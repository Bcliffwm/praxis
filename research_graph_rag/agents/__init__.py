"""
Agents package for Research GraphRAG.

Contains specialized agents for different types of research analysis.
"""

from .base_agent import ResearchQueryAgent
from .relationship_agent import EnhancedResearchQueryAgent
from .network_agent import NetworkAnalysisAgent
from .work_discovery_agent import WorkBasedDiscoveryAgent

__all__ = [
    "ResearchQueryAgent",
    "EnhancedResearchQueryAgent", 
    "NetworkAnalysisAgent",
    "WorkBasedDiscoveryAgent"
]