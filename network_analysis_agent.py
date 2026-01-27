#!/usr/bin/env python3
"""
Network Analysis Agent with Neo4j Graph Data Science

Uses Neo4j's Graph Data Science library to find related works through:
- Connectivity analysis (degree centrality)
- Shortest path analysis
- Betweenness centrality
- Closeness centrality  
- Community detection (Louvain algorithm)
- PageRank and other centrality measures

Provides numeric metrics like confidence scores and centrality magnitudes.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from research_query_agent import ResearchQueryAgent, ConfigManager, CypherValidator

# Graph Data Science query templates
GDS_QUERY_TEMPLATES = {
    "create_projection": """
        CALL gds.graph.project(
            $graph_name,
            ['Author', 'Work', 'Topic'],
            {
                WORK_AUTHORED_BY: {orientation: 'UNDIRECTED'},
                WORK_HAS_TOPIC: {orientation: 'UNDIRECTED'}
            }
        )
        YIELD graphName, nodeCount, relationshipCount
        RETURN graphName, nodeCount, relationshipCount
    """,
    
    "degree_centrality": """
        CALL gds.degree.stream($graph_name)
        YIELD nodeId, score
        WITH gds.util.asNode(nodeId) AS node, score
        WHERE node:Work
        RETURN node.id AS work_id, node.title AS title, score AS degree_centrality
        ORDER BY score DESC
        LIMIT $limit
    """,
    
    "betweenness_centrality": """
        CALL gds.betweenness.stream($graph_name)
        YIELD nodeId, score
        WITH gds.util.asNode(nodeId) AS node, score
        WHERE node:Work AND score > 0
        RETURN node.id AS work_id, node.title AS title, score AS betweenness_centrality
        ORDER BY score DESC
        LIMIT $limit
    """,
    
    "closeness_centrality": """
        CALL gds.closeness.stream($graph_name)
        YIELD nodeId, score
        WITH gds.util.asNode(nodeId) AS node, score
        WHERE node:Work AND score > 0
        RETURN node.id AS work_id, node.title AS title, score AS closeness_centrality
        ORDER BY score DESC
        LIMIT $limit
    """,
    
    "pagerank": """
        CALL gds.pageRank.stream($graph_name)
        YIELD nodeId, score
        WITH gds.util.asNode(nodeId) AS node, score
        WHERE node:Work
        RETURN node.id AS work_id, node.title AS title, score AS pagerank_score
        ORDER BY score DESC
        LIMIT $limit
    """,
    
    "community_detection": """
        CALL gds.louvain.stream($graph_name)
        YIELD nodeId, communityId
        WITH gds.util.asNode(nodeId) AS node, communityId
        WHERE node:Work
        RETURN node.id AS work_id, node.title AS title, communityId AS community_id
        ORDER BY communityId, work_id
    """,
    
    "shortest_path": """
        MATCH (source:Work), (target:Work)
        WHERE source.title CONTAINS $source_keyword AND target.id <> source.id
        WITH source, target
        LIMIT 1
        CALL gds.shortestPath.dijkstra.stream($graph_name, {
            sourceNode: source,
            targetNode: target
        })
        YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
        RETURN 
            gds.util.asNode(sourceNode).title AS source_title,
            gds.util.asNode(targetNode).title AS target_title,
            totalCost,
            size(nodeIds) AS path_length,
            [nodeId IN nodeIds | gds.util.asNode(nodeId).title] AS path_titles
        ORDER BY totalCost ASC
        LIMIT $limit
    """,
    
    "node_similarity": """
        CALL gds.nodeSimilarity.stream($graph_name)
        YIELD node1, node2, similarity
        WITH gds.util.asNode(node1) AS work1, gds.util.asNode(node2) AS work2, similarity
        WHERE work1:Work AND work2:Work AND similarity > $min_similarity
        RETURN 
            work1.id AS work1_id, work1.title AS work1_title,
            work2.id AS work2_id, work2.title AS work2_title,
            similarity AS similarity_score
        ORDER BY similarity DESC
        LIMIT $limit
    """,
    
    "find_related_by_centrality": """
        // Find target work
        MATCH (target:Work)
        WHERE target.title CONTAINS $title_keyword OR target.id = $work_id
        WITH target
        LIMIT 1
        
        // Get centrality scores for all works
        CALL gds.pageRank.stream($graph_name)
        YIELD nodeId, score AS pagerank
        WITH target, gds.util.asNode(nodeId) AS node, pagerank
        WHERE node:Work
        
        // Get community information
        CALL gds.louvain.stream($graph_name)
        YIELD nodeId AS commNodeId, communityId
        WITH target, node, pagerank, 
             CASE WHEN id(node) = commNodeId THEN communityId ELSE null END AS community
        WHERE community IS NOT NULL
        
        // Find works in same community or with high centrality
        WITH target, node, pagerank, community,
             CASE WHEN id(target) = commNodeId THEN communityId ELSE null END AS target_community
        WHERE target_community IS NOT NULL
        
        RETURN 
            target.title AS target_work,
            node.id AS related_work_id,
            node.title AS related_work_title,
            pagerank AS centrality_score,
            community AS community_id,
            CASE WHEN community = target_community THEN 1.0 ELSE 0.0 END AS same_community,
            pagerank * CASE WHEN community = target_community THEN 2.0 ELSE 1.0 END AS confidence_score
        ORDER BY confidence_score DESC
        LIMIT $limit
    """,
    
    "comprehensive_network_analysis": """
        // Find target work
        MATCH (target:Work)
        WHERE target.title CONTAINS $title_keyword OR target.id = $work_id
        WITH target
        LIMIT 1
        
        // Get all centrality measures
        CALL gds.degree.stream($graph_name)
        YIELD nodeId AS degreeNodeId, score AS degree
        
        CALL gds.betweenness.stream($graph_name)
        YIELD nodeId AS betweennessNodeId, score AS betweenness
        
        CALL gds.closeness.stream($graph_name)
        YIELD nodeId AS closenessNodeId, score AS closeness
        
        CALL gds.pageRank.stream($graph_name)
        YIELD nodeId AS pagerankNodeId, score AS pagerank
        
        CALL gds.louvain.stream($graph_name)
        YIELD nodeId AS communityNodeId, communityId
        
        // Combine all metrics
        WITH target,
             COLLECT({nodeId: degreeNodeId, score: degree}) AS degreeScores,
             COLLECT({nodeId: betweennessNodeId, score: betweenness}) AS betweennessScores,
             COLLECT({nodeId: closenessNodeId, score: closeness}) AS closenessScores,
             COLLECT({nodeId: pagerankNodeId, score: pagerank}) AS pagerankScores,
             COLLECT({nodeId: communityNodeId, communityId: communityId}) AS communityData
        
        // Process and return results
        UNWIND degreeScores AS degreeScore
        WITH target, degreeScore, betweennessScores, closenessScores, pagerankScores, communityData
        WHERE gds.util.asNode(degreeScore.nodeId):Work
        
        WITH target, 
             gds.util.asNode(degreeScore.nodeId) AS work,
             degreeScore.score AS degree,
             [bs IN betweennessScores WHERE bs.nodeId = degreeScore.nodeId | bs.score][0] AS betweenness,
             [cs IN closenessScores WHERE cs.nodeId = degreeScore.nodeId | cs.score][0] AS closeness,
             [ps IN pagerankScores WHERE ps.nodeId = degreeScore.nodeId | ps.score][0] AS pagerank,
             [cd IN communityData WHERE cd.nodeId = degreeScore.nodeId | cd.communityId][0] AS community
        
        WHERE work.id <> target.id
        
        // Calculate composite confidence score
        WITH target, work, degree, betweenness, closeness, pagerank, community,
             (COALESCE(degree, 0) * 0.2 + 
              COALESCE(betweenness, 0) * 0.3 + 
              COALESCE(closeness, 0) * 0.2 + 
              COALESCE(pagerank, 0) * 0.3) AS composite_score
        
        RETURN 
            target.title AS target_work,
            work.id AS related_work_id,
            work.title AS related_work_title,
            degree AS degree_centrality,
            betweenness AS betweenness_centrality,
            closeness AS closeness_centrality,
            pagerank AS pagerank_score,
            community AS community_id,
            composite_score AS confidence_score
        ORDER BY composite_score DESC
        LIMIT $limit
    """
}

# Network analysis result processing
class NetworkAnalysisResult:
    """Container for network analysis results with metrics."""
    
    def __init__(self, work_id: str, title: str, metrics: Dict[str, float]):
        self.work_id = work_id
        self.title = title
        self.metrics = metrics
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


class NetworkAnalysisAgent(ResearchQueryAgent):
    """Enhanced research query agent with Neo4j Graph Data Science capabilities."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize network analysis agent."""
        super().__init__(config_manager)
        self.graph_name = "research_network"
        self.gds_templates = GDS_QUERY_TEMPLATES
        self._graph_created = False
    
    def setup_agent(self):
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

Shortest Path Analysis:
CALL gds.shortestPath.dijkstra.stream('research_network', {
    sourceNode: source_work,
    targetNode: target_work
})
YIELD totalCost, nodeIds, path

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
        
        from strands import Agent
        
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
                return True
            
            # Create graph projection
            create_query = self.gds_templates["create_projection"]
            result = self.neo4j_tool(create_query, graph_name=self.graph_name)
            
            if result.get('error'):
                return False
            
            self._graph_created = True
            return True
            
        except Exception as e:
            print(f"Error creating graph projection: {e}")
            return False
    
    def find_related_by_network_analysis(self, title_keyword: str = None, work_id: str = None, 
                                       analysis_types: List[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Find related works using comprehensive network analysis."""
        if not title_keyword and not work_id:
            return {"error": "Either title_keyword or work_id must be provided"}
        
        # Ensure graph projection exists
        if not self.ensure_graph_projection():
            return {"error": "Failed to create graph projection for network analysis"}
        
        if analysis_types is None:
            analysis_types = ["comprehensive", "community", "centrality"]
        
        results = {}
        
        for analysis_type in analysis_types:
            try:
                if analysis_type == "comprehensive":
                    query = self.gds_templates["comprehensive_network_analysis"]
                elif analysis_type == "community":
                    query = self.gds_templates["find_related_by_centrality"]
                elif analysis_type == "centrality":
                    query = self.gds_templates["pagerank"]
                elif analysis_type == "shortest_path":
                    query = self.gds_templates["shortest_path"]
                elif analysis_type == "similarity":
                    query = self.gds_templates["node_similarity"]
                else:
                    continue
                
                params = {
                    "graph_name": self.graph_name,
                    "limit": limit
                }
                
                if title_keyword:
                    params["title_keyword"] = title_keyword
                    params["source_keyword"] = title_keyword
                if work_id:
                    params["work_id"] = work_id
                if analysis_type == "similarity":
                    params["min_similarity"] = 0.1
                
                result = self.neo4j_tool(query, **params)
                results[analysis_type] = self._process_network_results(result, analysis_type)
                
            except Exception as e:
                results[analysis_type] = {"error": str(e)}
        
        return {
            "query_type": "network_analysis",
            "input": {"title_keyword": title_keyword, "work_id": work_id},
            "analysis_types": analysis_types,
            "results": results,
            "graph_projection": self.graph_name
        }
    
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
            except Exception as e:
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
            
            return {
                "query_type": "community_detection",
                "result": processed_result,
                "graph_projection": self.graph_name
            }
        except Exception as e:
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
            community_stats.append({
                'community_id': community_id,
                'size': len(works),
                'works': works[:5],  # Show first 5 works
                'total_works': len(works)
            })
        
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
        
        from strands import tool
        
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
                return {
                    "error": "gds_query_validation_error",
                    "message": str(e),
                    "original_cypher": cypher
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
                
                return {
                    "row_count": len(records),
                    "records": records,
                    "query_parameters": params,
                    "gds_enabled": "gds." in safe_cypher.lower()
                }
            except Exception as e:
                return {
                    "error": "query_execution_error", 
                    "message": str(e),
                    "cypher": safe_cypher
                }
            finally:
                try:
                    client.close()
                except:
                    pass
        
        return network_analysis_neo4j_tool
    
    def _prepare_gds_query(self, cypher: str) -> str:
        """Prepare and validate GDS queries."""
        # Allow GDS procedure calls
        if "CALL gds." in cypher:
            return cypher
        
        # Apply basic validation for non-GDS queries
        CypherValidator.assert_read_only(cypher)
        return cypher


def main():
    """Main function to demonstrate network analysis capabilities."""
    try:
        # Initialize network analysis agent
        config_manager = ConfigManager()
        network_agent = NetworkAnalysisAgent(config_manager)
        
        print("Network Analysis Agent with Neo4j GDS Demo")
        print("=" * 60)
        
        # Example network analysis queries
        test_queries = [
            "Find works related to 'Collaborative Research' using network centrality analysis",
            "Show me the most central works in the research network using PageRank",
            "Detect research communities and show community structure",
            "Find works similar to 'Clinical Characteristics' using network topology"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 40)
            
            try:
                response = network_agent.query(query)
                # Show truncated response for demo
                response_str = str(response)
                if len(response_str) > 300:
                    print(f"{response_str[:300]}...\n[Response truncated for demo]")
                else:
                    print(response_str)
            except Exception as e:
                print(f"Error: {e}")
        
        # Demonstrate direct method calls
        print(f"\n{'='*60}")
        print("Direct Method Demonstrations")
        print("=" * 60)
        
        # Get centrality metrics
        print("\n1. Centrality Metrics:")
        centrality_result = network_agent.get_centrality_metrics(limit=5)
        print(f"Result keys: {list(centrality_result.keys())}")
        
        # Detect communities
        print("\n2. Community Detection:")
        community_result = network_agent.detect_communities()
        print(f"Result keys: {list(community_result.keys())}")
        
        # Network analysis for specific work
        print("\n3. Network Analysis for Specific Work:")
        analysis_result = network_agent.find_related_by_network_analysis(
            title_keyword="Collaborative Research", 
            limit=5
        )
        print(f"Result keys: {list(analysis_result.keys())}")
        
    except Exception as e:
        print(f"Failed to initialize network analysis agent: {e}")


if __name__ == "__main__":
    main()