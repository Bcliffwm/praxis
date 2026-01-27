"""
Enhanced relationship agent for author relationship inference.

Extends the base research query agent with enhanced capabilities for inferring
author relationships, co-authorship patterns, and latent research connections.
"""

import re
import logging
from typing import Dict, List, Any
from strands import Agent, tool

from .base_agent import ResearchQueryAgent
from ..core.config import ConfigManager
from ..core.database import Neo4jClient
from ..utils.validators import EnhancedCypherValidator
from ..utils.exceptions import GraphRAGError

logger = logging.getLogger(__name__)

# Enhanced relationship definitions for author relationship inference
ENHANCED_VALID_RELATIONSHIPS = {
    "WORK_AUTHORED_BY": {
        "from": "Author",
        "to": "Work", 
        "direction": "OUT",
        "description": "Author wrote/authored a work"
    },
    "WORK_HAS_TOPIC": {
        "from": "Work",
        "to": "Topic",
        "direction": "OUT",
        "description": "Work is associated with a topic"
    },
    # Inferred relationships for co-authorship analysis
    "COLLABORATED_WITH": {
        "from": "Author",
        "to": "Author",
        "direction": "BOTH",
        "description": "Authors who have co-authored works together",
        "inferred": True
    },
    "SHARES_TOPIC_WITH": {
        "from": "Author", 
        "to": "Author",
        "direction": "BOTH",
        "description": "Authors who work on similar topics",
        "inferred": True
    },
    "RELATED_TO": {
        "from": "Work",
        "to": "Work",
        "direction": "BOTH", 
        "description": "Works that are related to each other"
    }
}

# Enhanced Cypher patterns for relationship inference
RELATIONSHIP_INFERENCE_PATTERNS = {
    "coauthorship": {
        "pattern": """
        MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
        WHERE a1 <> a2
        """,
        "description": "Find authors who have co-authored works together"
    },
    "collaboration_network": {
        "pattern": """
        MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(coauthor:Author)
        WHERE a <> coauthor
        WITH a, COUNT(DISTINCT coauthor) as collaborator_count, COLLECT(DISTINCT coauthor.name) as collaborators
        """,
        "description": "Find collaboration networks and patterns"
    },
    "shared_topics": {
        "pattern": """
        MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
        WHERE a1 <> a2
        """,
        "description": "Find authors who work on similar topics"
    },
    "indirect_collaboration": {
        "pattern": """
        MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)<-[:WORK_AUTHORED_BY]-(bridge:Author)-[:WORK_AUTHORED_BY]->(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
        WHERE a1 <> a2 AND a1 <> bridge AND a2 <> bridge
        AND NOT EXISTS((a1)-[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]-(a2))
        """,
        "description": "Find potential collaborations through common co-authors"
    }
}


class EnhancedResearchQueryAgent(ResearchQueryAgent):
    """Enhanced research query agent with improved relationship inference capabilities."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize enhanced agent with relationship inference capabilities."""
        super().__init__(config_manager)
        self.relationship_patterns = RELATIONSHIP_INFERENCE_PATTERNS
        logger.info("Enhanced Research Query Agent initialized with relationship inference")
    
    def setup_agent(self) -> Agent:
        """Set up enhanced agent with improved system prompt for relationship inference."""
        system_prompt = """
You are an advanced research assistant that can query a Neo4j graph database containing academic research data.

Database Schema:
- Author nodes: Researchers and academics
- Work nodes: Academic papers, publications, research works  
- Topic nodes: Research topics and subject areas

Relationships:
- WORK_AUTHORED_BY: Author -> Work (authors write works)
- WORK_HAS_TOPIC: Work -> Topic (works are associated with topics)
- RELATED_TO: Work -> Work (works are related to each other)

Relationship Inference Capabilities:
You can infer complex relationships between authors including:
1. Co-authorship: Authors who have worked together on the same publications
2. Collaboration networks: Groups of authors who frequently collaborate
3. Shared research interests: Authors working on similar topics
4. Indirect connections: Authors connected through mutual collaborators
5. Research domain clustering: Groups of authors in similar research areas

Query Patterns for Relationship Inference:

Co-authorship Detection:
MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
WHERE a1 <> a2
RETURN a1.name, a2.name, w.title

Collaboration Networks:
MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(coauthor:Author)
WHERE a <> coauthor
WITH a, COUNT(DISTINCT coauthor) as collaborator_count
RETURN a.name, collaborator_count
ORDER BY collaborator_count DESC

Shared Topics:
MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
WHERE a1 <> a2
RETURN a1.name, a2.name, t.display_name

Indirect Collaborations:
MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)<-[:WORK_AUTHORED_BY]-(bridge:Author)-[:WORK_AUTHORED_BY]->(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
WHERE a1 <> a2 AND a1 <> bridge AND a2 <> bridge
AND NOT EXISTS((a1)-[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]-(a2))
RETURN a1.name, a2.name, bridge.name as connecting_author

Rules:
- Always use READ-ONLY Cypher queries
- Focus on relationship patterns between authors
- Use appropriate WHERE clauses to filter out self-relationships (a1 <> a2)
- Consider using WITH clauses for aggregations and complex patterns
- Return meaningful results that show relationships and connections

When asked about author relationships, collaborations, or research connections, 
use these patterns to construct appropriate Cypher queries.
        """
        
        agent = Agent(
            model=self.bedrock_model,
            tools=[self.neo4j_tool],
            system_prompt=system_prompt.strip()
        )
        
        return agent
    
    def create_neo4j_tool(self):
        """Create enhanced neo4j_query_tool with relationship inference support."""
        neo4j_config = self.config_manager.get_neo4j_config()
        
        @tool(
            name="neo4j_query_tool",
            description="Execute a READ-ONLY Cypher query against Neo4j with enhanced relationship inference"
        )
        def enhanced_neo4j_query_tool(cypher: str, **kwargs) -> dict:
            """Execute enhanced Cypher query with relationship inference support."""
            try:
                # Enhanced validation and preparation
                safe_cypher = EnhancedCypherValidator.prepare_cypher(cypher)
                safe_cypher = EnhancedCypherValidator.enhance_query_for_relationships(safe_cypher)
                EnhancedCypherValidator.validate_enhanced_relationships(safe_cypher)
                EnhancedCypherValidator.validate_properties(safe_cypher)
            except Exception as e:
                logger.warning(f"Enhanced Cypher validation failed: {e}")
                return {
                    "error": "enhanced_cypher_validation_error",
                    "message": str(e),
                    "original_cypher": cypher,
                    "suggestion": self._suggest_relationship_query(cypher)
                }
            
            # Execute query using database client
            try:
                with Neo4jClient(
                    uri=neo4j_config['uri'],
                    auth=neo4j_config['auth'],
                    database=neo4j_config['database']
                ) as client:
                    # Add parameters from kwargs
                    params = {k: v for k, v in kwargs.items() if k != 'cypher'}
                    records = client.run_cypher(safe_cypher, params)
                    
                    # Enhanced result processing for relationship queries
                    enhanced_results = self._enhance_relationship_results(records, safe_cypher)
                    
                    return {
                        "row_count": len(records),
                        "records": records,
                        "enhanced_analysis": enhanced_results,
                        "query_parameters": params
                    }
                    
            except GraphRAGError as e:
                logger.error(f"Enhanced query execution failed: {e}")
                return {
                    "error": "query_execution_error", 
                    "message": str(e),
                    "cypher": safe_cypher,
                    "suggestion": self._suggest_relationship_query(cypher)
                }
            except Exception as e:
                logger.error(f"Unexpected error during enhanced query execution: {e}")
                return {
                    "error": "unexpected_error",
                    "message": f"Unexpected error: {e}",
                    "cypher": safe_cypher
                }
        
        return enhanced_neo4j_query_tool
    
    def _suggest_relationship_query(self, original_query: str) -> str:
        """Suggest improved relationship queries based on the original query."""
        query_lower = original_query.lower()
        
        if "co-author" in query_lower or "collaborated" in query_lower:
            return "Try: MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author) WHERE a1 <> a2 RETURN a1.name, a2.name, w.title"
        
        elif "network" in query_lower or "collaboration" in query_lower:
            return "Try: MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(coauthor:Author) WHERE a <> coauthor WITH a, COUNT(DISTINCT coauthor) as collaborator_count RETURN a.name, collaborator_count ORDER BY collaborator_count DESC"
        
        elif "topic" in query_lower or "similar" in query_lower:
            return "Try: MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author) WHERE a1 <> a2 RETURN a1.name, a2.name, t.display_name"
        
        elif "potential" in query_lower or "indirect" in query_lower:
            return "Try: MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)<-[:WORK_AUTHORED_BY]-(bridge:Author)-[:WORK_AUTHORED_BY]->(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author) WHERE a1 <> a2 AND a1 <> bridge AND a2 <> bridge AND NOT EXISTS((a1)-[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]-(a2)) RETURN a1.name, a2.name, bridge.name"
        
        return "Consider using relationship patterns like WORK_AUTHORED_BY to find connections between authors"
    
    def _enhance_relationship_results(self, records: List[Dict], cypher: str) -> Dict[str, Any]:
        """Enhance results with relationship analysis."""
        if not records:
            return {"analysis": "No relationships found"}
        
        analysis = {
            "total_relationships": len(records),
            "relationship_type": self._identify_relationship_type(cypher),
            "insights": []
        }
        
        # Add specific insights based on query type
        if "co-author" in cypher.lower() or "WORK_AUTHORED_BY" in cypher:
            unique_authors = set()
            for record in records:
                for key, value in record.items():
                    if "name" in key.lower() and isinstance(value, str):
                        unique_authors.add(value)
            
            analysis["insights"].append(f"Found {len(unique_authors)} unique authors in collaboration network")
            
            if len(records) > len(unique_authors):
                analysis["insights"].append("Some authors have multiple collaborations")
        
        # Add topic analysis if topics are involved
        if "WORK_HAS_TOPIC" in cypher:
            topics = set()
            for record in records:
                for key, value in record.items():
                    if "topic" in key.lower() or "display_name" in key.lower():
                        if isinstance(value, str):
                            topics.add(value)
            
            if topics:
                analysis["insights"].append(f"Research spans {len(topics)} different topics")
                analysis["topics"] = list(topics)[:10]  # Top 10 topics
        
        return analysis
    
    def _identify_relationship_type(self, cypher: str) -> str:
        """Identify the type of relationship being queried."""
        cypher_lower = cypher.lower()
        
        if "work_authored_by" in cypher_lower and "work_has_topic" in cypher_lower:
            return "topic_collaboration"
        elif "work_authored_by" in cypher_lower:
            return "co_authorship"
        elif "work_has_topic" in cypher_lower:
            return "topic_relationship"
        elif "related_to" in cypher_lower:
            return "work_relationship"
        else:
            return "general_relationship"
    
    def find_coauthorship_relationships(self, author_name: str = None, limit: int = 20) -> Dict[str, Any]:
        """Find co-authorship relationships for a specific author or all authors."""
        try:
            if author_name:
                query = """
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE a1.name CONTAINS $author_name AND a1 <> a2
                RETURN a1.name AS author1, a2.name AS author2, w.title AS shared_work
                ORDER BY a1.name, a2.name
                LIMIT $limit
                """
                params = {"author_name": author_name, "limit": limit}
            else:
                query = """
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE a1 <> a2
                WITH a1, a2, COUNT(w) AS collaboration_count, COLLECT(w.title) AS shared_works
                WHERE collaboration_count > 1
                RETURN a1.name AS author1, a2.name AS author2, 
                       collaboration_count, shared_works
                ORDER BY collaboration_count DESC
                LIMIT $limit
                """
                params = {"limit": limit}
            
            result = self.neo4j_tool(query, **params)
            
            return {
                "query_type": "coauthorship_relationships",
                "author_filter": author_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Failed to find coauthorship relationships: {e}")
            return {"error": str(e)}
    
    def find_collaboration_networks(self, min_collaborators: int = 2, limit: int = 20) -> Dict[str, Any]:
        """Find authors with the most collaboration networks."""
        try:
            query = """
            MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(coauthor:Author)
            WHERE a <> coauthor
            WITH a, COUNT(DISTINCT coauthor) AS collaborator_count, 
                 COLLECT(DISTINCT coauthor.name) AS collaborators
            WHERE collaborator_count >= $min_collaborators
            RETURN a.name AS author, collaborator_count, collaborators
            ORDER BY collaborator_count DESC
            LIMIT $limit
            """
            
            params = {"min_collaborators": min_collaborators, "limit": limit}
            result = self.neo4j_tool(query, **params)
            
            return {
                "query_type": "collaboration_networks",
                "min_collaborators": min_collaborators,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Failed to find collaboration networks: {e}")
            return {"error": str(e)}
    
    def find_shared_topic_relationships(self, topic_name: str = None, limit: int = 20) -> Dict[str, Any]:
        """Find authors who share research topics."""
        try:
            if topic_name:
                query = """
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE t.display_name CONTAINS $topic_name AND a1 <> a2
                RETURN a1.name AS author1, a2.name AS author2, t.display_name AS shared_topic,
                       w1.title AS work1, w2.title AS work2
                ORDER BY t.display_name, a1.name
                LIMIT $limit
                """
                params = {"topic_name": topic_name, "limit": limit}
            else:
                query = """
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE a1 <> a2
                WITH a1, a2, t, COUNT(*) AS shared_topic_count
                WHERE shared_topic_count > 1
                RETURN a1.name AS author1, a2.name AS author2, t.display_name AS shared_topic,
                       shared_topic_count
                ORDER BY shared_topic_count DESC, t.display_name
                LIMIT $limit
                """
                params = {"limit": limit}
            
            result = self.neo4j_tool(query, **params)
            
            return {
                "query_type": "shared_topic_relationships",
                "topic_filter": topic_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Failed to find shared topic relationships: {e}")
            return {"error": str(e)}
    
    def find_indirect_collaborations(self, limit: int = 20) -> Dict[str, Any]:
        """Find potential collaborations through mutual co-authors."""
        try:
            query = """
            MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)<-[:WORK_AUTHORED_BY]-(bridge:Author)-[:WORK_AUTHORED_BY]->(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
            WHERE a1 <> a2 AND a1 <> bridge AND a2 <> bridge
            AND NOT EXISTS((a1)-[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]-(a2))
            WITH a1, a2, bridge, COUNT(*) AS connection_strength
            RETURN a1.name AS author1, a2.name AS author2, bridge.name AS connecting_author,
                   connection_strength
            ORDER BY connection_strength DESC
            LIMIT $limit
            """
            
            params = {"limit": limit}
            result = self.neo4j_tool(query, **params)
            
            return {
                "query_type": "indirect_collaborations",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Failed to find indirect collaborations: {e}")
            return {"error": str(e)}