"""
Neo4j Graph Data Science query templates.

Contains pre-built query templates for various GDS algorithms and network analysis.
"""

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
    """,
    
    "graph_exists": """
        CALL gds.graph.exists($graph_name) 
        YIELD exists
        RETURN exists
    """,
    
    "drop_graph": """
        CALL gds.graph.drop($graph_name) 
        YIELD graphName
        RETURN graphName
    """,
    
    "graph_info": """
        CALL gds.graph.list($graph_name)
        YIELD graphName, nodeCount, relationshipCount, memoryUsage
        RETURN graphName, nodeCount, relationshipCount, memoryUsage
    """,
    
    "eigenvector_centrality": """
        CALL gds.eigenvector.stream($graph_name)
        YIELD nodeId, score
        WITH gds.util.asNode(nodeId) AS node, score
        WHERE node:Work AND score > 0
        RETURN node.id AS work_id, node.title AS title, score AS eigenvector_centrality
        ORDER BY score DESC
        LIMIT $limit
    """,
    
    "triangles": """
        CALL gds.triangles.stream($graph_name)
        YIELD nodeId, triangles
        WITH gds.util.asNode(nodeId) AS node, triangles
        WHERE node:Work AND triangles > 0
        RETURN node.id AS work_id, node.title AS title, triangles AS triangle_count
        ORDER BY triangles DESC
        LIMIT $limit
    """,
    
    "local_clustering_coefficient": """
        CALL gds.localClusteringCoefficient.stream($graph_name)
        YIELD nodeId, localClusteringCoefficient
        WITH gds.util.asNode(nodeId) AS node, localClusteringCoefficient
        WHERE node:Work AND localClusteringCoefficient > 0
        RETURN node.id AS work_id, node.title AS title, 
               localClusteringCoefficient AS clustering_coefficient
        ORDER BY localClusteringCoefficient DESC
        LIMIT $limit
    """,
    
    "weakly_connected_components": """
        CALL gds.wcc.stream($graph_name)
        YIELD nodeId, componentId
        WITH gds.util.asNode(nodeId) AS node, componentId
        WHERE node:Work
        RETURN node.id AS work_id, node.title AS title, componentId AS component_id
        ORDER BY componentId, work_id
    """,
    
    "strongly_connected_components": """
        CALL gds.scc.stream($graph_name)
        YIELD nodeId, componentId
        WITH gds.util.asNode(nodeId) AS node, componentId
        WHERE node:Work
        RETURN node.id AS work_id, node.title AS title, componentId AS component_id
        ORDER BY componentId, work_id
    """
}

# Query parameter templates
QUERY_PARAMETERS = {
    "default_limit": 20,
    "default_min_similarity": 0.1,
    "default_graph_name": "research_network",
    "centrality_weights": {
        "degree": 0.2,
        "betweenness": 0.3,
        "closeness": 0.2,
        "pagerank": 0.3
    }
}

# Analysis type configurations
ANALYSIS_CONFIGS = {
    "comprehensive": {
        "algorithms": ["degree", "betweenness", "closeness", "pagerank", "louvain"],
        "description": "Full network analysis with all centrality measures and community detection"
    },
    "centrality": {
        "algorithms": ["degree", "betweenness", "closeness", "pagerank"],
        "description": "Focus on centrality measures only"
    },
    "community": {
        "algorithms": ["louvain", "pagerank"],
        "description": "Community detection with PageRank scoring"
    },
    "similarity": {
        "algorithms": ["node_similarity"],
        "description": "Node similarity analysis"
    },
    "connectivity": {
        "algorithms": ["degree", "triangles", "local_clustering_coefficient"],
        "description": "Connectivity and clustering analysis"
    },
    "components": {
        "algorithms": ["weakly_connected_components", "strongly_connected_components"],
        "description": "Connected components analysis"
    }
}