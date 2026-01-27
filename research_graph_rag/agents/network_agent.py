"""
Network analysis agent with Neo4j Graph Data Science capabilities.

Provides advanced network analysis using centrality measures, community detection,
and other graph algorithms for research relationship discovery.
"""

import logging
from typing import Dict, List, Any, Optional
from strands import Agent, tool

from .base_agent import ResearchQueryAgent
from ..core.config import ConfigManager
from ..core.database import Neo4jClient
from ..core.models import NetworkAnalysisResult, NetworkAnalysisConfig, CommunityInfo
from ..utils.validators import CypherValidator
from ..utils.exceptions import GraphRAGError
from ..utils.gds_queries import GDS_QUERY_TEMPLATES

logger = logging.getLogger(__name__)


class NetworkAnalysisAgent(ResearchQueryAgent):
    """Enhanced research query agent with Neo4j Graph Data Science capabilities."""
    
    def __init__(self, config_manager: ConfigManager, graph_name: str = "research_network"):
        """Initialize network analysis agent.
        
        Args:
            config_manager: Configuration manager instance
            graph_name: Name for the graph projection in Neo4j GDS
        """
        self.graph_name = graph_name
        self.gds_templates = GDS_QUERY_TEMPLATES
        self._graph_created = False
        super().__init__(config_manager)
        logger.info(f"Network Analysis Agent initialized with graph: {graph_name}")
    
    def setup_agent(self) -> Agent:
        """Set up enhanced agent with network analysis capabilities."""
        system_prompt = """
You are an advanced research assistant that uses Neo4j Graph Data Science to analyze research networks.
You specialize in finding related works using sophisticated network analysis metrics.

Database Schema:
- Author nodes: Researchers and academics
- Work nodes: Academic papers, publications, research works  
- Topic nodes: Research topics and subject areas

Relationships:
- WORK_AUTHORED_BY: Author -> Work (authors write works)
- WORK_HAS_TOPIC: Work -> Topic (works are associated with topics)

Network Analysis Capabilities:
You can find related works using advanced graph algorithms and centrality measures:

1. **Degree Centrality**: Measures connectivity (how many relationships a work has)
2. **Betweenness Centrality**: Identifies works that lie on many shortest paths between other works
3. **Closeness Centrality**: Finds works with optimal traversal paths to other works
4. **PageRank**: Measures importance based on the network structure
5. **Community Detection**: Groups works into communities using Louvain algorithm
6. **Shortest Path Analysis**: Finds optimal paths between works in the network
7. **Node Similarity**: Identifies works with similar network neighborhoods

Query Patterns for Network Analysis:

Find Works by Centrality:
CALL gds.pageRank.stream('research_network')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE node:Work
RETURN node.title, score ORDER BY score DESC

Community Detection:
CALL gds.louvain.stream('research_network')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS node, communityId
WHERE node:Work
RETURN node.title, communityId

Network-Based Related Works Discovery:
When given a work title, use multiple centrality measures and community detection
to find related works with confidence scores based on network topology.

Rules:
- Always ensure the graph projection exists before running GDS algorithms
- Use multiple centrality measures for comprehensive analysis
- Provide confidence scores based on composite metrics
- Include community information for clustering insights
- Return numeric metrics for interpretability

When asked about finding related works using network analysis, construct appropriate
GDS queries and provide detailed metric explanations.
        """
        
        agent = Agent(
            model=self.bedrock_model,
            tools=[self.neo4j_tool],
            system_prompt=system_prompt.strip()
        )
        
        return agent
    
    def ensure_graph_projection(self) -> bool:
        """Ensure the graph projection exists for GDS algorithms."""
        try:
            # Check if graph exists
            check_query = "CALL gds.graph.exists($graph_name) YIELD exists"
            result = self.neo4j_tool(check_query, graph_name=self.graph_name)
            
            if result.get('records') and result['records'][0].get('exists'):
                self._graph_created = True
                logger.debug(f"Graph projection '{self.graph_name}' already exists")
                return True
            
            # Create graph projection
            create_query = self.gds_templates["create_projection"]
            result = self.neo4j_tool(create_query, graph_name=self.graph_name)
            
            if result.get('error'):
                logger.error(f"Failed to create graph projection: {result['error']}")
                return False
            
            self._graph_created = True
            logger.info(f"Graph projection '{self.graph_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating graph projection: {e}")
            return False
    
    def find_related_by_network_analysis(
        self, 
        title_keyword: str = None, 
        work_id: str = None,
        config: Optional[NetworkAnalysisConfig] = None
    ) -> Dict[str, Any]:
        """Find related works using comprehensive network analysis.
        
        Args:
            title_keyword: Keyword to search in work titles
            work_id: Specific work ID to analyze
            config: Network analysis configuration
            
        Returns:
            Dictionary containing analysis results with metrics
        """
        if not title_keyword and not work_id:
            return {"error": "Either title_keyword or work_id must be provided"}
        
        # Use default config if not provided
        if config is None:
            config = NetworkAnalysisConfig()
        
        # Ensure graph projection exists
        if not self.ensure_graph_projection():
            return {"error": "Failed to create graph projection for network analysis"}
        
        results = {}
        analysis_types = config.validate_analysis_types()
        
        for analysis_type in analysis_types:
            try:
                result = self._run_analysis_type(
                    analysis_type, title_keyword, work_id, config
                )
                results[analysis_type] = self._process_network_results(result, analysis_type)
                
            except Exception as e:
                logger.error(f"Analysis type '{analysis_type}' failed: {e}")
                results[analysis_type] = {"error": str(e)}
        
        return {
            "query_type": "network_analysis",
            "input": {"title_keyword": title_keyword, "work_id": work_id},
            "analysis_types": analysis_types,
            "results": results,
            "graph_projection": self.graph_name,
            "config": config.dict()
        }
    
    def _run_analysis_type(
        self, 
        analysis_type: str, 
        title_keyword: str, 
        work_id: str, 
        config: NetworkAnalysisConfig
    ) -> Dict[str, Any]:
        """Run a specific type of network analysis."""
        query_map = {
            "comprehensive": "comprehensive_network_analysis",
            "community": "find_related_by_centrality", 
            "centrality": "pagerank",
            "shortest_path": "shortest_path",
            "similarity": "node_similarity"
        }
        
        query_template = query_map.get(analysis_type)
        if not query_template or query_template not in self.gds_templates:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
        
        query = self.gds_templates[query_template]
        params = {
            "graph_name": self.graph_name,
            "limit": config.limit
        }
        
        if title_keyword:
            params["title_keyword"] = title_keyword
            params["source_keyword"] = title_keyword
        if work_id:
            params["work_id"] = work_id
        if analysis_type == "similarity":
            params["min_similarity"] = 0.1
        
        return self.neo4j_tool(query, **params)
    
    def get_centrality_metrics(self, limit: int = 20) -> Dict[str, Any]:
        """Get centrality metrics for all works in the network."""
        if not self.ensure_graph_projection():
            return {"error": "Failed to create graph projection"}
        
        metrics = {}
        centrality_types = ["degree_centrality", "betweenness_centrality", "closeness_centrality", "pagerank"]
        
        for centrality_type in centrality_types:
            try:
                query = self.gds_templates[centrality_type]
                params = {"graph_name": self.graph_name, "limit": limit}
                result = self.neo4j_tool(query, **params)
                metrics[centrality_type] = result
                logger.debug(f"Retrieved {centrality_type} metrics")
            except Exception as e:
                logger.error(f"Failed to get {centrality_type}: {e}")
                metrics[centrality_type] = {"error": str(e)}
        
        return {
            "query_type": "centrality_metrics",
            "metrics": metrics,
            "graph_projection": self.graph_name
        }
    
    def detect_communities(self) -> Dict[str, Any]:
        """Detect communities in the research network."""
        if not self.ensure_graph_projection():
            return {"error": "Failed to create graph projection"}
        
        try:
            query = self.gds_templates["community_detection"]
            params = {"graph_name": self.graph_name}
            result = self.neo4j_tool(query, **params)
            
            # Process community results
            processed_result = self._process_community_results(result)
            
            logger.info(f"Community detection completed: {processed_result.get('total_communities', 0)} communities found")
            
            return {
                "query_type": "community_detection",
                "result": processed_result,
                "graph_projection": self.graph_name
            }
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return {"error": str(e)}
    
    def _process_network_results(self, result: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Process network analysis results with enhanced metrics."""
        if result.get('error'):
            return result
        
        records = result.get('records', [])
        if not records:
            return {"message": "No results found", "count": 0}
        
        processed_records = []
        
        for record in records:
            processed_record = dict(record)
            
            # Add confidence score calculation
            if analysis_type == "comprehensive":
                confidence = self._calculate_composite_confidence(record)
                processed_record['confidence_score'] = confidence
            elif analysis_type == "community":
                confidence = record.get('confidence_score', 0.0)
                processed_record['confidence_score'] = confidence
            else:
                # Use the main metric as confidence for single-metric analyses
                main_metric = self._get_main_metric(record, analysis_type)
                processed_record['confidence_score'] = main_metric
            
            processed_records.append(processed_record)
        
        # Sort by confidence score
        processed_records.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        return {
            "count": len(processed_records),
            "records": processed_records,
            "analysis_type": analysis_type,
            "metrics_included": self._get_metrics_list(analysis_type)
        }
    
    def _calculate_composite_confidence(self, record: Dict[str, Any]) -> float:
        """Calculate composite confidence score from multiple centrality measures."""
        weights = {
            'degree_centrality': 0.2,
            'betweenness_centrality': 0.3,
            'closeness_centrality': 0.2,
            'pagerank_score': 0.3
        }
        
        score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            value = record.get(metric)
            if value is not None and value > 0:
                score += weight * float(value)
                total_weight += weight
        
        # Normalize to 0-1 range
        normalized_score = score / total_weight if total_weight > 0 else 0.0
        
        # Boost for same community
        if record.get('community_id') is not None:
            normalized_score *= 1.2
        
        return min(normalized_score, 1.0)
    
    def _get_main_metric(self, record: Dict[str, Any], analysis_type: str) -> float:
        """Get the main metric value for confidence scoring."""
        metric_map = {
            "centrality": "pagerank_score",
            "community": "pagerank_score", 
            "shortest_path": "totalCost",
            "similarity": "similarity_score"
        }
        
        metric_key = metric_map.get(analysis_type, "score")
        value = record.get(metric_key, 0.0)
        
        # Normalize different metric types
        if analysis_type == "shortest_path":
            # Invert cost (lower cost = higher confidence)
            return 1.0 / (1.0 + float(value)) if value > 0 else 0.0
        else:
            return float(value) if value is not None else 0.0
    
    def _get_metrics_list(self, analysis_type: str) -> List[str]:
        """Get list of metrics included in the analysis."""
        metric_lists = {
            "comprehensive": ["degree_centrality", "betweenness_centrality", "closeness_centrality", "pagerank_score", "community_id"],
            "community": ["pagerank_score", "community_id", "same_community"],
            "centrality": ["pagerank_score"],
            "shortest_path": ["totalCost", "path_length"],
            "similarity": ["similarity_score"]
        }
        
        return metric_lists.get(analysis_type, ["score"])
    
    def _process_community_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process community detection results."""
        if result.get('error'):
            return result
        
        records = result.get('records', [])
        if not records:
            return {"message": "No communities found", "count": 0}
        
        # Group by community
        communities = {}
        for record in records:
            community_id = record.get('community_id')
            if community_id not in communities:
                communities[community_id] = []
            communities[community_id].append({
                'work_id': record.get('work_id'),
                'title': record.get('title')
            })
        
        # Calculate community statistics
        community_stats = []
        for community_id, works in communities.items():
            community_info = CommunityInfo(
                community_id=community_id,
                size=len(works),
                works=works[:5],  # Show first 5 works
                total_works=len(works)
            )
            community_stats.append(community_info.dict())
        
        # Sort by community size
        community_stats.sort(key=lambda x: x['size'], reverse=True)
        
        return {
            "total_communities": len(communities),
            "total_works": len(records),
            "communities": community_stats,
            "largest_community_size": max(len(works) for works in communities.values()) if communities else 0
        }
    
    def create_neo4j_tool(self):
        """Create enhanced neo4j_query_tool with GDS support."""
        neo4j_config = self.config_manager.get_neo4j_config()
        
        @tool(
            name="neo4j_query_tool",
            description="Execute Neo4j queries including Graph Data Science algorithms"
        )
        def network_analysis_neo4j_tool(cypher: str, **kwargs) -> dict:
            """Execute Neo4j query with GDS support."""
            try:
                # Enhanced validation for GDS queries
                safe_cypher = self._prepare_gds_query(cypher)
            except Exception as e:
                logger.warning(f"GDS query validation failed: {e}")
                return {
                    "error": "gds_query_validation_error",
                    "message": str(e),
                    "original_cypher": cypher
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
                    
                    return {
                        "row_count": len(records),
                        "records": records,
                        "query_parameters": params,
                        "gds_enabled": "gds." in safe_cypher.lower()
                    }
                    
            except GraphRAGError as e:
                logger.error(f"GDS query execution failed: {e}")
                return {
                    "error": "query_execution_error", 
                    "message": str(e),
                    "cypher": safe_cypher
                }
            except Exception as e:
                logger.error(f"Unexpected error during GDS query: {e}")
                return {
                    "error": "unexpected_error",
                    "message": f"Unexpected error: {e}",
                    "cypher": safe_cypher
                }
        
        return network_analysis_neo4j_tool
    
    def _prepare_gds_query(self, cypher: str) -> str:
        """Prepare and validate GDS queries."""
        # Allow GDS procedure calls
        if "CALL gds." in cypher:
            logger.debug("GDS query detected, allowing procedure call")
            return cypher
        
        # Apply basic validation for non-GDS queries
        CypherValidator.assert_read_only(cypher)
        return cypher
    
    def drop_graph_projection(self) -> bool:
        """Drop the current graph projection."""
        try:
            drop_query = "CALL gds.graph.drop($graph_name) YIELD graphName"
            result = self.neo4j_tool(drop_query, graph_name=self.graph_name)
            
            if not result.get('error'):
                self._graph_created = False
                logger.info(f"Graph projection '{self.graph_name}' dropped successfully")
                return True
            else:
                logger.warning(f"Failed to drop graph projection: {result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Error dropping graph projection: {e}")
            return False
    
    def get_graph_info(self) -> Dict[str, Any]:
        """Get information about the current graph projection."""
        try:
            info_query = """
            CALL gds.graph.list($graph_name)
            YIELD graphName, nodeCount, relationshipCount, memoryUsage
            RETURN graphName, nodeCount, relationshipCount, memoryUsage
            """
            result = self.neo4j_tool(info_query, graph_name=self.graph_name)
            
            if result.get('records'):
                return {
                    "graph_exists": True,
                    "graph_info": result['records'][0]
                }
            else:
                return {
                    "graph_exists": False,
                    "message": "Graph projection does not exist"
                }
                
        except Exception as e:
            logger.error(f"Error getting graph info: {e}")
            return {
                "graph_exists": False,
                "error": str(e)
            }