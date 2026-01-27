#!/usr/bin/env python3
"""
Enhanced Research Query Agent with Author Relationship Inference

Extends the base research query agent with enhanced capabilities for inferring
author relationships, co-authorship patterns, and latent research connections.
"""

import re
from typing import Dict, List, Any
from research_query_agent import ResearchQueryAgent, ConfigManager, CypherValidator

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


class EnhancedCypherValidator(CypherValidator):
    """Enhanced Cypher validator with support for relationship inference patterns."""
    
    @staticmethod
    def validate_enhanced_relationships(cypher: str) -> None:
        """Validate relationships including inferred ones."""
        # Get all relationship types from the query
        relationships = re.findall(r":([A-Za-z_][A-Za-z0-9_]*)", cypher)
        
        for rel in relationships:
            # Check against enhanced relationship definitions
            if rel not in ENHANCED_VALID_RELATIONSHIPS and rel not in {"Author", "Work", "Topic"}:
                # Allow some common relationship inference patterns
                inference_patterns = [
                    "COLLABORATED_WITH",
                    "SHARES_TOPIC_WITH", 
                    "CO_AUTHORED",
                    "WORKS_WITH"
                ]
                
                if rel not in inference_patterns:
                    raise ValueError(f"Unknown relationship: {rel}")
    
    @staticmethod
    def enhance_query_for_relationships(cypher: str) -> str:
        """Enhance queries to better support relationship inference."""
        # Replace common relationship aliases with patterns
        enhancements = {
            # Co-authorship patterns
            r"COLLABORATED_WITH": "[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]",
            r"CO_AUTHORED": "[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]",
            
            # Topic sharing patterns  
            r"SHARES_TOPIC_WITH": "[:WORK_AUTHORED_BY]->(:Work)-[:WORK_HAS_TOPIC]->(:Topic)<-[:WORK_HAS_TOPIC]-(:Work)<-[:WORK_AUTHORED_BY]",
        }
        
        enhanced_cypher = cypher
        for pattern, replacement in enhancements.items():
            enhanced_cypher = re.sub(f"-\\[:{pattern}\\]->", f"-{replacement}-", enhanced_cypher)
        
        return enhanced_cypher


class EnhancedResearchQueryAgent(ResearchQueryAgent):
    """Enhanced research query agent with improved relationship inference capabilities."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize enhanced agent with relationship inference capabilities."""
        super().__init__(config_manager)
        self.relationship_patterns = RELATIONSHIP_INFERENCE_PATTERNS
    
    def setup_agent(self):
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
        
        from strands import Agent
        
        agent = Agent(
            model=self.bedrock_model,
            tools=[self.neo4j_tool],
            system_prompt=system_prompt.strip()
        )
        
        return agent
    
    def create_neo4j_tool(self):
        """Create enhanced neo4j_query_tool with relationship inference support."""
        neo4j_config = self.config_manager.get_neo4j_config()
        
        from strands import tool
        
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
                return {
                    "error": "enhanced_cypher_validation_error",
                    "message": str(e),
                    "original_cypher": cypher,
                    "suggestion": self._suggest_relationship_query(cypher)
                }
            
            # Execute query using parent class method
            from research_query_agent import Neo4jClient
            
            try:
                client = Neo4jClient(
                    uri=neo4j_config['uri'],
                    auth=neo4j_config['auth'],
                    database=neo4j_config['database']
                )
            except ValueError as e:
                return {
                    "error": "database_connection_error",
                    "message": str(e),
                    "cypher": safe_cypher
                }
            
            try:
                records = client.run_cypher(safe_cypher)
                
                # Enhanced result processing for relationship queries
                enhanced_results = self._enhance_relationship_results(records, safe_cypher)
                
                return {
                    "row_count": len(records),
                    "records": records,
                    "enhanced_analysis": enhanced_results
                }
            except ValueError as e:
                return {
                    "error": "query_execution_error", 
                    "message": str(e),
                    "cypher": safe_cypher,
                    "suggestion": self._suggest_relationship_query(cypher)
                }
            except Exception as e:
                return {
                    "error": "unexpected_error",
                    "message": f"Unexpected error during enhanced query execution: {e}",
                    "cypher": safe_cypher
                }
            finally:
                try:
                    client.close()
                except:
                    pass
        
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


def main():
    """Main function to demonstrate enhanced relationship inference capabilities."""
    try:
        # Initialize enhanced agent
        config_manager = ConfigManager()
        enhanced_agent = EnhancedResearchQueryAgent(config_manager)
        
        # Example relationship inference queries
        test_queries = [
            "Find authors who have co-authored works together",
            "Show me the most collaborative authors in the database",
            "Which authors work on similar research topics?",
            "Find potential research collaborations based on shared interests"
        ]
        
        print("Enhanced Research Query Agent - Relationship Inference Demo")
        print("=" * 60)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 40)
            
            try:
                response = enhanced_agent.query(query)
                print(f"Response: {response}")
            except Exception as e:
                print(f"Error: {e}")
        
    except Exception as e:
        print(f"Failed to initialize enhanced agent: {e}")


if __name__ == "__main__":
    main()