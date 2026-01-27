"""
Work-based discovery agent for finding related works.

Provides capabilities to find related works based on titles, award numbers,
authors, topics, and other work attributes using various relationship patterns.
"""

import logging
from typing import Dict, List, Any, Optional
from strands import Agent, tool

from .base_agent import ResearchQueryAgent
from ..core.config import ConfigManager
from ..core.database import Neo4jClient
from ..utils.validators import CypherValidator
from ..utils.exceptions import GraphRAGError

logger = logging.getLogger(__name__)


class WorkBasedDiscoveryAgent(ResearchQueryAgent):
    """Agent specialized in finding related works through various discovery methods."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize work-based discovery agent."""
        super().__init__(config_manager)
        logger.info("Work-Based Discovery Agent initialized")
    
    def setup_agent(self) -> Agent:
        """Set up agent with work discovery capabilities."""
        system_prompt = """
You are a research assistant specialized in finding related academic works using various discovery methods.

Database Schema:
- Author nodes: Researchers and academics with properties (id, name, cited_by_count, works_count)
- Work nodes: Academic papers and publications with properties (id, title, type, publication_date)
- Topic nodes: Research topics with properties (id, topic_name, description)

Relationships:
- WORK_AUTHORED_BY: Author -> Work (authors write works)
- WORK_HAS_TOPIC: Work -> Topic (works are associated with topics)
- RELATED_TO: Work -> Work (works are related to each other)

Work Discovery Capabilities:
You can find related works using multiple approaches:

1. **Title-based Discovery**: Find works with similar titles or keywords
2. **Author-based Discovery**: Find other works by the same authors
3. **Topic-based Discovery**: Find works sharing similar research topics
4. **Award-based Discovery**: Find works with shared funding or awards
5. **Citation-based Discovery**: Find works that cite or are cited by target works
6. **Hybrid Discovery**: Combine multiple methods for comprehensive results

Query Patterns for Work Discovery:

Find Works by Title Similarity:
MATCH (w:Work)
WHERE w.title CONTAINS $title_keyword
RETURN w.id, w.title, w.type, w.publication_date
ORDER BY w.title

Find Related Works by Shared Authors:
MATCH (target:Work)<-[:WORK_AUTHORED_BY]-(author:Author)-[:WORK_AUTHORED_BY]->(related:Work)
WHERE target.title CONTAINS $title_keyword AND target <> related
RETURN related.id, related.title, author.name
ORDER BY related.title

Find Related Works by Shared Topics:
MATCH (target:Work)-[:WORK_HAS_TOPIC]->(topic:Topic)<-[:WORK_HAS_TOPIC]-(related:Work)
WHERE target.title CONTAINS $title_keyword AND target <> related
RETURN related.id, related.title, topic.display_name
ORDER BY related.title

Find Works by Award Numbers:
MATCH (w:Work)
WHERE w.award_number = $award_number OR w.funding_info CONTAINS $award_number
RETURN w.id, w.title, w.award_number, w.funding_info

Comprehensive Related Works Discovery:
When given a work title or ID, use multiple relationship patterns to find
related works with relevance scoring based on connection strength.

Rules:
- Use READ-ONLY Cypher queries only
- Provide relevance scores when possible
- Include multiple discovery methods for comprehensive results
- Return structured results with work details and relationship context
- Use appropriate filtering and ordering for best results

When asked about finding related works, construct queries that explore
multiple relationship types and provide comprehensive discovery results.
        """
        
        agent = Agent(
            model=self.bedrock_model,
            tools=[self.neo4j_tool],
            system_prompt=system_prompt.strip()
        )
        
        return agent
    
    def find_related_works_by_title(self, title_keyword: str, limit: int = 20) -> Dict[str, Any]:
        """Find related works using title-based discovery methods."""
        try:
            # Multiple discovery approaches
            results = {}
            
            # 1. Direct title similarity
            title_similarity_query = """
            MATCH (w:Work)
            WHERE w.title CONTAINS $title_keyword
            RETURN w.id AS work_id, w.title AS title, w.type AS work_type, 
                   w.publication_date AS publication_date
            ORDER BY w.title
            LIMIT $limit
            """
            
            results["title_similarity"] = self.neo4j_tool(
                title_similarity_query, 
                title_keyword=title_keyword, 
                limit=limit
            )
            
            # 2. Related works by shared authors
            shared_authors_query = """
            MATCH (target:Work)<-[:WORK_AUTHORED_BY]-(author:Author)-[:WORK_AUTHORED_BY]->(related:Work)
            WHERE target.title CONTAINS $title_keyword AND target <> related
            WITH related, author, COUNT(*) AS author_connection_strength
            RETURN related.id AS work_id, related.title AS title, 
                   COLLECT(author.name) AS shared_authors,
                   author_connection_strength
            ORDER BY author_connection_strength DESC, related.title
            LIMIT $limit
            """
            
            results["shared_authors"] = self.neo4j_tool(
                shared_authors_query,
                title_keyword=title_keyword,
                limit=limit
            )
            
            # 3. Related works by shared topics
            shared_topics_query = """
            MATCH (target:Work)-[:WORK_HAS_TOPIC]->(topic:Topic)<-[:WORK_HAS_TOPIC]-(related:Work)
            WHERE target.title CONTAINS $title_keyword AND target <> related
            WITH related, topic, COUNT(*) AS topic_connection_strength
            RETURN related.id AS work_id, related.title AS title,
                   COLLECT(topic.display_name) AS shared_topics,
                   topic_connection_strength
            ORDER BY topic_connection_strength DESC, related.title
            LIMIT $limit
            """
            
            results["shared_topics"] = self.neo4j_tool(
                shared_topics_query,
                title_keyword=title_keyword,
                limit=limit
            )
            
            # 4. Comprehensive discovery with scoring
            comprehensive_query = """
            MATCH (target:Work)
            WHERE target.title CONTAINS $title_keyword
            WITH target
            LIMIT 1
            
            // Find related works through multiple paths
            OPTIONAL MATCH (target)<-[:WORK_AUTHORED_BY]-(author:Author)-[:WORK_AUTHORED_BY]->(author_related:Work)
            WHERE target <> author_related
            
            OPTIONAL MATCH (target)-[:WORK_HAS_TOPIC]->(topic:Topic)<-[:WORK_HAS_TOPIC]-(topic_related:Work)
            WHERE target <> topic_related
            
            OPTIONAL MATCH (target)-[:RELATED_TO]-(directly_related:Work)
            
            // Combine all related works
            WITH target, 
                 COLLECT(DISTINCT author_related) AS author_related_works,
                 COLLECT(DISTINCT topic_related) AS topic_related_works,
                 COLLECT(DISTINCT directly_related) AS directly_related_works
            
            // Process and score results
            UNWIND (author_related_works + topic_related_works + directly_related_works) AS related
            WHERE related IS NOT NULL
            
            WITH target, related,
                 CASE WHEN related IN author_related_works THEN 1 ELSE 0 END AS author_score,
                 CASE WHEN related IN topic_related_works THEN 1 ELSE 0 END AS topic_score,
                 CASE WHEN related IN directly_related_works THEN 2 ELSE 0 END AS direct_score
            
            WITH target, related, 
                 (author_score + topic_score + direct_score) AS relevance_score
            
            RETURN target.title AS target_work,
                   related.id AS related_work_id,
                   related.title AS related_work_title,
                   relevance_score,
                   author_score > 0 AS shared_authors,
                   topic_score > 0 AS shared_topics,
                   direct_score > 0 AS directly_related
            ORDER BY relevance_score DESC, related.title
            LIMIT $limit
            """
            
            results["comprehensive"] = self.neo4j_tool(
                comprehensive_query,
                title_keyword=title_keyword,
                limit=limit
            )
            
            return {
                "query_type": "work_discovery_by_title",
                "title_keyword": title_keyword,
                "discovery_methods": list(results.keys()),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Failed to find related works by title: {e}")
            return {"error": str(e)}
    
    def find_works_by_award_number(self, award_number: str, limit: int = 20) -> Dict[str, Any]:
        """Find works associated with a specific award number."""
        try:
            # Direct award number match
            direct_match_query = """
            MATCH (w:Work)
            WHERE w.award_number = $award_number 
               OR w.funding_info CONTAINS $award_number
               OR w.grants CONTAINS $award_number
            RETURN w.id AS work_id, w.title AS title, w.award_number AS award_number,
                   w.funding_info AS funding_info, w.publication_date AS publication_date
            ORDER BY w.publication_date DESC
            LIMIT $limit
            """
            
            direct_results = self.neo4j_tool(
                direct_match_query,
                award_number=award_number,
                limit=limit
            )
            
            # Related works through shared funding
            related_funding_query = """
            MATCH (target:Work), (related:Work)
            WHERE (target.award_number = $award_number OR target.funding_info CONTAINS $award_number)
              AND target <> related
              AND (related.award_number = target.award_number 
                   OR related.funding_info CONTAINS target.award_number
                   OR target.funding_info CONTAINS related.award_number)
            RETURN target.title AS target_work,
                   related.id AS related_work_id,
                   related.title AS related_work_title,
                   related.award_number AS related_award_number,
                   related.funding_info AS related_funding_info
            ORDER BY related.title
            LIMIT $limit
            """
            
            related_results = self.neo4j_tool(
                related_funding_query,
                award_number=award_number,
                limit=limit
            )
            
            return {
                "query_type": "work_discovery_by_award",
                "award_number": award_number,
                "direct_matches": direct_results,
                "related_funding": related_results
            }
            
        except Exception as e:
            logger.error(f"Failed to find works by award number: {e}")
            return {"error": str(e)}
    
    def find_works_by_author(self, author_name: str, limit: int = 20) -> Dict[str, Any]:
        """Find works by a specific author and related works."""
        try:
            # Direct author works
            author_works_query = """
            MATCH (author:Author)-[:WORK_AUTHORED_BY]->(work:Work)
            WHERE author.name CONTAINS $author_name
            RETURN author.name AS author_name,
                   work.id AS work_id,
                   work.title AS title,
                   work.type AS work_type,
                   work.publication_date AS publication_date
            ORDER BY work.publication_date DESC
            LIMIT $limit
            """
            
            author_works = self.neo4j_tool(
                author_works_query,
                author_name=author_name,
                limit=limit
            )
            
            # Co-authored works (works by collaborators)
            collaborator_works_query = """
            MATCH (author:Author)-[:WORK_AUTHORED_BY]->(shared_work:Work)<-[:WORK_AUTHORED_BY]-(collaborator:Author)-[:WORK_AUTHORED_BY]->(other_work:Work)
            WHERE author.name CONTAINS $author_name 
              AND author <> collaborator
              AND shared_work <> other_work
            RETURN author.name AS target_author,
                   collaborator.name AS collaborator_name,
                   other_work.id AS work_id,
                   other_work.title AS title,
                   shared_work.title AS shared_work_title
            ORDER BY collaborator.name, other_work.title
            LIMIT $limit
            """
            
            collaborator_works = self.neo4j_tool(
                collaborator_works_query,
                author_name=author_name,
                limit=limit
            )
            
            return {
                "query_type": "work_discovery_by_author",
                "author_name": author_name,
                "author_works": author_works,
                "collaborator_works": collaborator_works
            }
            
        except Exception as e:
            logger.error(f"Failed to find works by author: {e}")
            return {"error": str(e)}
    
    def find_works_by_topic(self, topic_keyword: str, limit: int = 20) -> Dict[str, Any]:
        """Find works related to a specific topic."""
        try:
            # Direct topic match
            topic_works_query = """
            MATCH (topic:Topic)<-[:WORK_HAS_TOPIC]-(work:Work)
            WHERE topic.display_name CONTAINS $topic_keyword
               OR topic.description CONTAINS $topic_keyword
            RETURN topic.display_name AS topic_name,
                   work.id AS work_id,
                   work.title AS title,
                   work.type AS work_type,
                   work.publication_date AS publication_date
            ORDER BY topic.display_name, work.title
            LIMIT $limit
            """
            
            topic_works = self.neo4j_tool(
                topic_works_query,
                topic_keyword=topic_keyword,
                limit=limit
            )
            
            # Related topics and their works
            related_topics_query = """
            MATCH (target_topic:Topic)<-[:WORK_HAS_TOPIC]-(shared_work:Work)-[:WORK_HAS_TOPIC]->(related_topic:Topic)<-[:WORK_HAS_TOPIC]-(related_work:Work)
            WHERE target_topic.display_name CONTAINS $topic_keyword
              AND target_topic <> related_topic
              AND shared_work <> related_work
            WITH related_topic, COUNT(DISTINCT shared_work) AS connection_strength
            MATCH (related_topic)<-[:WORK_HAS_TOPIC]-(work:Work)
            RETURN related_topic.display_name AS related_topic_name,
                   connection_strength,
                   work.id AS work_id,
                   work.title AS title
            ORDER BY connection_strength DESC, related_topic.display_name, work.title
            LIMIT $limit
            """
            
            related_topics = self.neo4j_tool(
                related_topics_query,
                topic_keyword=topic_keyword,
                limit=limit
            )
            
            return {
                "query_type": "work_discovery_by_topic",
                "topic_keyword": topic_keyword,
                "topic_works": topic_works,
                "related_topics": related_topics
            }
            
        except Exception as e:
            logger.error(f"Failed to find works by topic: {e}")
            return {"error": str(e)}
    
    def comprehensive_work_discovery(self, 
                                   title_keyword: str = None,
                                   work_id: str = None,
                                   award_number: str = None,
                                   author_name: str = None,
                                   topic_keyword: str = None,
                                   limit: int = 20) -> Dict[str, Any]:
        """Comprehensive work discovery using multiple methods."""
        try:
            results = {}
            
            # Determine primary search method
            if work_id:
                primary_method = "work_id"
                primary_value = work_id
            elif title_keyword:
                primary_method = "title_keyword"
                primary_value = title_keyword
            elif award_number:
                primary_method = "award_number"
                primary_value = award_number
            elif author_name:
                primary_method = "author_name"
                primary_value = author_name
            elif topic_keyword:
                primary_method = "topic_keyword"
                primary_value = topic_keyword
            else:
                return {"error": "At least one search parameter must be provided"}
            
            # Execute relevant discovery methods
            if title_keyword:
                results["title_based"] = self.find_related_works_by_title(title_keyword, limit)
            
            if award_number:
                results["award_based"] = self.find_works_by_award_number(award_number, limit)
            
            if author_name:
                results["author_based"] = self.find_works_by_author(author_name, limit)
            
            if topic_keyword:
                results["topic_based"] = self.find_works_by_topic(topic_keyword, limit)
            
            # If work_id is provided, find related works for that specific work
            if work_id:
                work_specific_query = """
                MATCH (target:Work)
                WHERE target.id = $work_id
                
                // Find related through authors
                OPTIONAL MATCH (target)<-[:WORK_AUTHORED_BY]-(author:Author)-[:WORK_AUTHORED_BY]->(author_related:Work)
                WHERE target <> author_related
                
                // Find related through topics
                OPTIONAL MATCH (target)-[:WORK_HAS_TOPIC]->(topic:Topic)<-[:WORK_HAS_TOPIC]-(topic_related:Work)
                WHERE target <> topic_related
                
                // Find directly related
                OPTIONAL MATCH (target)-[:RELATED_TO]-(directly_related:Work)
                
                WITH target,
                     COLLECT(DISTINCT author_related) AS author_works,
                     COLLECT(DISTINCT topic_related) AS topic_works,
                     COLLECT(DISTINCT directly_related) AS direct_works
                
                UNWIND (author_works + topic_works + direct_works) AS related
                WHERE related IS NOT NULL
                
                RETURN target.title AS target_work,
                       related.id AS related_work_id,
                       related.title AS related_work_title,
                       related IN author_works AS shared_authors,
                       related IN topic_works AS shared_topics,
                       related IN direct_works AS directly_related
                ORDER BY related.title
                LIMIT $limit
                """
                
                results["work_id_based"] = self.neo4j_tool(
                    work_specific_query,
                    work_id=work_id,
                    limit=limit
                )
            
            return {
                "query_type": "comprehensive_work_discovery",
                "primary_method": primary_method,
                "primary_value": primary_value,
                "discovery_methods": list(results.keys()),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Failed comprehensive work discovery: {e}")
            return {"error": str(e)}