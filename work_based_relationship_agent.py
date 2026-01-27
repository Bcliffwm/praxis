#!/usr/bin/env python3
"""
Work-Based Relationship Agent

Extends the research query agent with capabilities to find related works based on:
- Work titles (content similarity)
- Award numbers (shared funding)
- Author overlap (collaborative connections)
- Topic relationships (thematic connections)
"""

import re
from typing import Dict, List, Any, Optional
from research_query_agent import ResearchQueryAgent, ConfigManager, CypherValidator

# Enhanced relationship patterns for work-based discovery
WORK_RELATIONSHIP_PATTERNS = {
    "title_similarity": {
        "pattern": """
        MATCH (w1:Work), (w2:Work)
        WHERE w1 <> w2 
        AND (w1.title CONTAINS $keyword OR w2.title CONTAINS $keyword)
        """,
        "description": "Find works with similar titles or keywords"
    },
    "shared_authors": {
        "pattern": """
        MATCH (w1:Work)<-[:WORK_AUTHORED_BY]-(a:Author)-[:WORK_AUTHORED_BY]->(w2:Work)
        WHERE w1 <> w2
        """,
        "description": "Find works that share common authors"
    },
    "shared_topics": {
        "pattern": """
        MATCH (w1:Work)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(w2:Work)
        WHERE w1 <> w2
        """,
        "description": "Find works that share common topics"
    },
    "related_works": {
        "pattern": """
        MATCH (w1:Work)-[:RELATED_TO]-(w2:Work)
        """,
        "description": "Find explicitly related works"
    },
    "award_based": {
        "pattern": """
        MATCH (w1:Work), (w2:Work)
        WHERE w1 <> w2 
        AND w1.award_number = w2.award_number
        AND w1.award_number IS NOT NULL
        """,
        "description": "Find works with the same award/grant number"
    }
}

# Enhanced Cypher patterns for work discovery
WORK_DISCOVERY_QUERIES = {
    "find_by_title": """
        MATCH (w:Work)
        WHERE w.title CONTAINS $title_keyword
        RETURN w.id, w.title, w.type, w.publication_date
        ORDER BY w.publication_date DESC
        LIMIT 10
    """,
    
    "find_related_by_title": """
        MATCH (target:Work)
        WHERE target.title CONTAINS $title_keyword OR target.id = $work_id
        WITH target
        
        // Find works by same authors
        MATCH (target)<-[:WORK_AUTHORED_BY]-(a:Author)-[:WORK_AUTHORED_BY]->(related:Work)
        WHERE related <> target
        WITH target, related, COUNT(a) as shared_authors
        
        RETURN target.title as original_work,
               related.id as related_id,
               related.title as related_title,
               related.type as related_type,
               shared_authors,
               'shared_authors' as relationship_type
        ORDER BY shared_authors DESC
        LIMIT 10
    """,
    
    "find_related_by_topics": """
        MATCH (target:Work)
        WHERE target.title CONTAINS $title_keyword OR target.id = $work_id
        WITH target
        
        // Find works with shared topics
        MATCH (target)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(related:Work)
        WHERE related <> target
        WITH target, related, COUNT(t) as shared_topics, COLLECT(t.topic_name) as topics
        
        RETURN target.title as original_work,
               related.id as related_id,
               related.title as related_title,
               related.type as related_type,
               shared_topics,
               topics[0..3] as sample_topics,
               'shared_topics' as relationship_type
        ORDER BY shared_topics DESC
        LIMIT 10
    """,
    
    "find_by_award": """
        MATCH (w:Work)
        WHERE w.award_number = $award_number
        RETURN w.id, w.title, w.type, w.publication_date, w.award_number
        ORDER BY w.publication_date DESC
    """,
    
    "comprehensive_related_works": """
        MATCH (target:Work)
        WHERE target.title CONTAINS $title_keyword OR target.id = $work_id
        WITH target
        
        // Find all types of relationships
        OPTIONAL MATCH (target)<-[:WORK_AUTHORED_BY]-(a:Author)-[:WORK_AUTHORED_BY]->(author_related:Work)
        WHERE author_related <> target
        
        OPTIONAL MATCH (target)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(topic_related:Work)
        WHERE topic_related <> target
        
        OPTIONAL MATCH (target)-[:RELATED_TO]-(explicit_related:Work)
        
        WITH target,
             COLLECT(DISTINCT {work: author_related, type: 'shared_authors'}) as author_rels,
             COLLECT(DISTINCT {work: topic_related, type: 'shared_topics'}) as topic_rels,
             COLLECT(DISTINCT {work: explicit_related, type: 'explicit_relation'}) as explicit_rels
        
        WITH target, author_rels + topic_rels + explicit_rels as all_relations
        UNWIND all_relations as rel
        WHERE rel.work IS NOT NULL
        
        RETURN target.title as original_work,
               rel.work.id as related_id,
               rel.work.title as related_title,
               rel.work.type as related_type,
               rel.type as relationship_type
        LIMIT 20
    """
}


class WorkBasedRelationshipAgent(ResearchQueryAgent):
    """Enhanced research query agent with work-based relationship discovery capabilities."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize work-based relationship agent."""
        super().__init__(config_manager)
        self.work_patterns = WORK_RELATIONSHIP_PATTERNS
        self.discovery_queries = WORK_DISCOVERY_QUERIES
    
    def setup_agent(self):
        """Set up enhanced agent with work-based relationship discovery capabilities."""
        system_prompt = """
You are an advanced research assistant that can query a Neo4j graph database containing academic research data.
You specialize in finding related works based on various relationship types.

Database Schema:
- Author nodes: Researchers and academics
- Work nodes: Academic papers, publications, research works  
- Topic nodes: Research topics and subject areas

Relationships:
- WORK_AUTHORED_BY: Author -> Work (authors write works)
- WORK_HAS_TOPIC: Work -> Topic (works are associated with topics)
- RELATED_TO: Work -> Work (works are related to each other)

Work-Based Relationship Discovery Capabilities:
You can find related works through multiple relationship types:

1. **Title-Based Discovery**: Find works with similar titles or keywords
2. **Author-Based Relationships**: Find works by the same authors
3. **Topic-Based Relationships**: Find works sharing common research topics
4. **Award-Based Relationships**: Find works funded by the same grants/awards
5. **Explicit Relationships**: Find works with direct RELATED_TO connections

Query Patterns for Work Discovery:

Find Works by Title Keyword:
MATCH (w:Work)
WHERE w.title CONTAINS "keyword"
RETURN w.id, w.title, w.type, w.publication_date

Find Related Works by Shared Authors:
MATCH (target:Work {id: "work_id"})<-[:WORK_AUTHORED_BY]-(a:Author)-[:WORK_AUTHORED_BY]->(related:Work)
WHERE related <> target
RETURN target.title, related.title, COUNT(a) as shared_authors

Find Related Works by Shared Topics:
MATCH (target:Work {id: "work_id"})-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(related:Work)
WHERE related <> target
RETURN target.title, related.title, COLLECT(t.topic_name) as shared_topics

Find Works by Award Number:
MATCH (w:Work)
WHERE w.award_number = "award_123"
RETURN w.id, w.title, w.award_number

Comprehensive Related Works Discovery:
MATCH (target:Work)
WHERE target.title CONTAINS "keyword" OR target.id = "work_id"
OPTIONAL MATCH (target)<-[:WORK_AUTHORED_BY]-(a:Author)-[:WORK_AUTHORED_BY]->(author_related:Work)
OPTIONAL MATCH (target)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(topic_related:Work)
RETURN target.title, author_related.title, topic_related.title

Input Processing Guidelines:
- When given a work title, search for exact matches first, then partial matches
- When given an award number, find all works with that award number
- When asked for "related works", use comprehensive discovery combining multiple relationship types
- Always explain the type of relationship found (shared authors, topics, awards, etc.)

Rules:
- Always use READ-ONLY Cypher queries
- Focus on work-to-work relationships
- Use CONTAINS for partial title matching
- Include relationship strength indicators (count of shared authors/topics)
- Return meaningful results showing how works are connected

When asked about finding related works, use these patterns to construct appropriate Cypher queries.
        """
        
        from strands import Agent
        
        agent = Agent(
            model=self.bedrock_model,
            tools=[self.neo4j_tool],
            system_prompt=system_prompt.strip()
        )
        
        return agent
    
    def find_works_by_title(self, title_keyword: str) -> Dict[str, Any]:
        """Find works containing a specific title keyword."""
        try:
            query = self.discovery_queries["find_by_title"]
            
            # Use the neo4j tool directly
            result = self.neo4j_tool(query, title_keyword=title_keyword)
            
            return {
                "query_type": "find_by_title",
                "keyword": title_keyword,
                "result": result
            }
        except Exception as e:
            return {
                "query_type": "find_by_title",
                "keyword": title_keyword,
                "error": str(e)
            }
    
    def find_related_works(self, title_keyword: str = None, work_id: str = None, 
                          relationship_types: List[str] = None) -> Dict[str, Any]:
        """Find works related to a target work through various relationship types."""
        if not title_keyword and not work_id:
            return {"error": "Either title_keyword or work_id must be provided"}
        
        if relationship_types is None:
            relationship_types = ["shared_authors", "shared_topics", "comprehensive"]
        
        results = {}
        
        for rel_type in relationship_types:
            try:
                if rel_type == "shared_authors":
                    query = self.discovery_queries["find_related_by_title"]
                elif rel_type == "shared_topics":
                    query = self.discovery_queries["find_related_by_topics"]
                elif rel_type == "comprehensive":
                    query = self.discovery_queries["comprehensive_related_works"]
                else:
                    continue
                
                params = {}
                if title_keyword:
                    params["title_keyword"] = title_keyword
                if work_id:
                    params["work_id"] = work_id
                
                result = self.neo4j_tool(query, **params)
                results[rel_type] = result
                
            except Exception as e:
                results[rel_type] = {"error": str(e)}
        
        return {
            "query_type": "find_related_works",
            "input": {"title_keyword": title_keyword, "work_id": work_id},
            "relationship_types": relationship_types,
            "results": results
        }
    
    def find_works_by_award(self, award_number: str) -> Dict[str, Any]:
        """Find all works associated with a specific award number."""
        try:
            query = self.discovery_queries["find_by_award"]
            result = self.neo4j_tool(query, award_number=award_number)
            
            return {
                "query_type": "find_by_award",
                "award_number": award_number,
                "result": result
            }
        except Exception as e:
            return {
                "query_type": "find_by_award",
                "award_number": award_number,
                "error": str(e)
            }
    
    def create_neo4j_tool(self):
        """Create enhanced neo4j_query_tool with work-based relationship discovery support."""
        neo4j_config = self.config_manager.get_neo4j_config()
        
        from strands import tool
        
        @tool(
            name="neo4j_query_tool",
            description="Execute a READ-ONLY Cypher query against Neo4j with work-based relationship discovery"
        )
        def work_based_neo4j_query_tool(cypher: str, **kwargs) -> dict:
            """Execute enhanced Cypher query with work-based relationship discovery support."""
            try:
                # Enhanced validation for work-based queries
                safe_cypher = self._prepare_work_query(cypher)
                CypherValidator.validate_properties(safe_cypher)
            except Exception as e:
                return {
                    "error": "work_query_validation_error",
                    "message": str(e),
                    "original_cypher": cypher,
                    "suggestion": self._suggest_work_query(cypher)
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
                # Add parameters from kwargs
                params = {k: v for k, v in kwargs.items() if k != 'cypher'}
                records = client.run_cypher(safe_cypher, params)
                
                # Enhanced result processing for work-based queries
                enhanced_results = self._enhance_work_results(records, safe_cypher, params)
                
                return {
                    "row_count": len(records),
                    "records": records,
                    "enhanced_analysis": enhanced_results,
                    "query_parameters": params
                }
            except ValueError as e:
                return {
                    "error": "query_execution_error", 
                    "message": str(e),
                    "cypher": safe_cypher,
                    "suggestion": self._suggest_work_query(cypher)
                }
            except Exception as e:
                return {
                    "error": "unexpected_error",
                    "message": f"Unexpected error during work query execution: {e}",
                    "cypher": safe_cypher
                }
            finally:
                try:
                    client.close()
                except:
                    pass
        
        return work_based_neo4j_query_tool
    
    def _prepare_work_query(self, cypher: str) -> str:
        """Prepare and validate work-based queries."""
        # Basic validation
        CypherValidator.assert_read_only(cypher)
        
        # Enhance work-specific patterns
        enhanced_cypher = self._enhance_work_patterns(cypher)
        
        return enhanced_cypher
    
    def _enhance_work_patterns(self, cypher: str) -> str:
        """Enhance queries with work-specific patterns."""
        # Replace common work relationship aliases
        enhancements = {
            r"SIMILAR_TO": "[:WORK_HAS_TOPIC]->(:Topic)<-[:WORK_HAS_TOPIC]",
            r"SAME_AUTHOR": "[:WORK_AUTHORED_BY]<-(:Author)-[:WORK_AUTHORED_BY]->",
            r"FUNDED_BY": ".award_number",
        }
        
        enhanced_cypher = cypher
        for pattern, replacement in enhancements.items():
            enhanced_cypher = re.sub(f"-\\[:{pattern}\\]->", f"-{replacement}-", enhanced_cypher)
        
        return enhanced_cypher
    
    def _suggest_work_query(self, original_query: str) -> str:
        """Suggest improved work-based queries."""
        query_lower = original_query.lower()
        
        if "title" in query_lower and "similar" in query_lower:
            return "Try: MATCH (w:Work) WHERE w.title CONTAINS 'keyword' RETURN w.id, w.title"
        
        elif "related" in query_lower or "similar" in query_lower:
            return "Try: MATCH (w1:Work)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(w2:Work) WHERE w1 <> w2 RETURN w1.title, w2.title, t.topic_name"
        
        elif "author" in query_lower and "same" in query_lower:
            return "Try: MATCH (w1:Work)<-[:WORK_AUTHORED_BY]-(a:Author)-[:WORK_AUTHORED_BY]->(w2:Work) WHERE w1 <> w2 RETURN w1.title, w2.title, a.name"
        
        elif "award" in query_lower or "grant" in query_lower:
            return "Try: MATCH (w:Work) WHERE w.award_number = 'award_123' RETURN w.id, w.title, w.award_number"
        
        return "Consider using work title keywords, award numbers, or relationship patterns like WORK_HAS_TOPIC"
    
    def _enhance_work_results(self, records: List[Dict], cypher: str, params: Dict) -> Dict[str, Any]:
        """Enhance results with work-based relationship analysis."""
        if not records:
            return {"analysis": "No related works found"}
        
        analysis = {
            "total_works": len(records),
            "query_type": self._identify_work_query_type(cypher),
            "parameters_used": list(params.keys()),
            "insights": []
        }
        
        # Add specific insights based on query type
        if "WORK_HAS_TOPIC" in cypher:
            topics = set()
            for record in records:
                for key, value in record.items():
                    if "topic" in key.lower() and isinstance(value, (str, list)):
                        if isinstance(value, list):
                            topics.update(value)
                        else:
                            topics.add(value)
            
            if topics:
                analysis["insights"].append(f"Found connections through {len(topics)} different topics")
                analysis["sample_topics"] = list(topics)[:5]
        
        if "WORK_AUTHORED_BY" in cypher:
            authors = set()
            for record in records:
                for key, value in record.items():
                    if "author" in key.lower() and isinstance(value, str):
                        authors.add(value)
            
            if authors:
                analysis["insights"].append(f"Found connections through {len(authors)} different authors")
        
        # Analyze relationship strength
        if any("shared" in str(record).lower() for record in records):
            analysis["insights"].append("Results include relationship strength indicators")
        
        return analysis
    
    def _identify_work_query_type(self, cypher: str) -> str:
        """Identify the type of work-based query."""
        cypher_lower = cypher.lower()
        
        if "award_number" in cypher_lower:
            return "award_based_discovery"
        elif "work_has_topic" in cypher_lower:
            return "topic_based_discovery"
        elif "work_authored_by" in cypher_lower:
            return "author_based_discovery"
        elif "title contains" in cypher_lower:
            return "title_based_discovery"
        elif "related_to" in cypher_lower:
            return "explicit_relationship_discovery"
        else:
            return "general_work_discovery"


def main():
    """Main function to demonstrate work-based relationship discovery."""
    try:
        # Initialize work-based agent
        config_manager = ConfigManager()
        work_agent = WorkBasedRelationshipAgent(config_manager)
        
        # Example work-based discovery queries
        test_queries = [
            "Find works with titles containing 'Collaborative Research'",
            "Show me works related to 'Clinical Characteristics of Coronavirus Disease'",
            "Find all works by the same authors as 'Multi-Author Investigation'",
            "What works share topics with studies about collaborative research?",
        ]
        
        print("Work-Based Relationship Discovery Agent Demo")
        print("=" * 60)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 40)
            
            try:
                response = work_agent.query(query)
                # Show truncated response for demo
                response_str = str(response)
                if len(response_str) > 300:
                    print(f"{response_str[:300]}...\n[Response truncated for demo]")
                else:
                    print(response_str)
            except Exception as e:
                print(f"Error: {e}")
        
    except Exception as e:
        print(f"Failed to initialize work-based agent: {e}")


if __name__ == "__main__":
    main()