# Network Analysis Guide with Neo4j Graph Data Science

## Overview
This guide shows how to use work titles as input to find related works using advanced network analysis metrics including connectivity, shortest paths, centrality measures, and community detection with Neo4j's Graph Data Science library.

## Key Features

### 🎯 Network Metrics Available
- **Degree Centrality**: Measures connectivity (how many relationships a work has)
- **Betweenness Centrality**: Identifies works that lie on many shortest paths
- **Closeness Centrality**: Finds works with optimal traversal paths to others
- **PageRank**: Measures importance based on network structure
- **Community Detection**: Groups works using Louvain algorithm
- **Shortest Path Analysis**: Finds optimal paths between works
- **Node Similarity**: Identifies works with similar network neighborhoods

### 📊 Numeric Metrics Provided
- **Confidence Scores**: Composite scores from multiple centrality measures (0.0-1.0)
- **Centrality Magnitudes**: Precise numeric values for each centrality measure
- **Community IDs**: Numeric identifiers for detected communities
- **Path Lengths**: Exact distances in network topology
- **Similarity Scores**: Quantified similarity between works (0.0-1.0)

## Quick Start

### 1. Basic Setup
```python
from network_analysis_agent import NetworkAnalysisAgent, ConfigManager

# Initialize the agent
config_manager = ConfigManager()
agent = NetworkAnalysisAgent(config_manager)
```

### 2. Find Related Works Using Network Analysis
```python
# Comprehensive network analysis
result = agent.find_related_by_network_analysis(
    title_keyword="Machine Learning",
    analysis_types=["comprehensive", "community"],
    limit=10
)

# Extract confidence scores and metrics
for record in result['results']['comprehensive']['records']:
    print(f"Work: {record['related_work_title']}")
    print(f"Confidence: {record['confidence_score']:.4f}")
    print(f"PageRank: {record['pagerank_score']:.6f}")
    print(f"Betweenness: {record['betweenness_centrality']:.6f}")
    print(f"Community: {record['community_id']}")
```

### 3. Get Centrality Metrics
```python
# Get centrality metrics for top works
centrality_result = agent.get_centrality_metrics(limit=20)

# Access different centrality measures
pagerank_scores = centrality_result['metrics']['pagerank']['records']
betweenness_scores = centrality_result['metrics']['betweenness_centrality']['records']
degree_scores = centrality_result['metrics']['degree_centrality']['records']
```

### 4. Detect Research Communities
```python
# Detect communities using Louvain algorithm
community_result = agent.detect_communities()

print(f"Total communities: {community_result['total_communities']}")
print(f"Largest community: {community_result['largest_community_size']} works")

# Access community details
for community in community_result['communities']:
    print(f"Community {community['community_id']}: {community['size']} works")
```

## Network Analysis Methods

### 1. Comprehensive Network Analysis
**Use Case**: Get complete network analysis with all centrality measures and confidence scores.

```python
result = agent.find_related_by_network_analysis(
    title_keyword="Deep Learning in Healthcare",
    analysis_types=["comprehensive"],
    limit=15
)

# Result structure:
{
    "query_type": "network_analysis",
    "results": {
        "comprehensive": {
            "count": 15,
            "records": [
                {
                    "related_work_id": "W123456",
                    "related_work_title": "Neural Networks for Medical Diagnosis",
                    "degree_centrality": 0.045,
                    "betweenness_centrality": 0.0023,
                    "closeness_centrality": 0.234,
                    "pagerank_score": 0.0012,
                    "community_id": 5,
                    "confidence_score": 0.8745
                }
            ]
        }
    }
}
```

### 2. Centrality-Based Discovery
**Use Case**: Find the most influential works in the network.

```python
# Get works with highest PageRank scores
centrality_result = agent.get_centrality_metrics(limit=10)

# Access PageRank results
pagerank_works = centrality_result['metrics']['pagerank']['records']
for work in pagerank_works:
    print(f"{work['title']}: PageRank = {work['pagerank_score']:.6f}")

# Access betweenness centrality (bridge works)
betweenness_works = centrality_result['metrics']['betweenness_centrality']['records']
for work in betweenness_works:
    print(f"{work['title']}: Betweenness = {work['betweenness_centrality']:.6f}")
```

### 3. Community-Based Discovery
**Use Case**: Find works in the same research community.

```python
result = agent.find_related_by_network_analysis(
    title_keyword="Climate Change Research",
    analysis_types=["community"],
    limit=10
)

# Works in same community get higher confidence scores
community_results = result['results']['community']['records']
for work in community_results:
    same_community = work.get('same_community', 0)
    confidence = work['confidence_score']
    print(f"{work['related_work_title']}")
    print(f"Same Community: {'Yes' if same_community else 'No'}")
    print(f"Confidence: {confidence:.4f}")
```

### 4. Shortest Path Analysis
**Use Case**: Find how works are connected through the network.

```python
result = agent.find_related_by_network_analysis(
    title_keyword="Quantum Computing",
    analysis_types=["shortest_path"],
    limit=5
)

# Access path information
path_results = result['results']['shortest_path']['records']
for path in path_results:
    print(f"From: {path['source_title']}")
    print(f"To: {path['target_title']}")
    print(f"Path Length: {path['path_length']}")
    print(f"Total Cost: {path['totalCost']:.4f}")
    print(f"Path: {' -> '.join(path['path_titles'])}")
```

## Advanced Usage Patterns

### 1. Multi-Metric Analysis
```python
def analyze_work_importance(title_keyword):
    """Analyze work importance using multiple metrics."""
    
    # Get comprehensive analysis
    result = agent.find_related_by_network_analysis(
        title_keyword=title_keyword,
        analysis_types=["comprehensive"],
        limit=20
    )
    
    # Extract and rank by different metrics
    works = result['results']['comprehensive']['records']
    
    # Rank by PageRank (importance)
    by_pagerank = sorted(works, key=lambda x: x['pagerank_score'], reverse=True)
    
    # Rank by betweenness (bridge importance)
    by_betweenness = sorted(works, key=lambda x: x['betweenness_centrality'], reverse=True)
    
    # Rank by composite confidence
    by_confidence = sorted(works, key=lambda x: x['confidence_score'], reverse=True)
    
    return {
        'most_important': by_pagerank[:5],
        'best_bridges': by_betweenness[:5],
        'highest_confidence': by_confidence[:5]
    }
```

### 2. Community Analysis
```python
def analyze_research_communities():
    """Analyze research community structure."""
    
    community_result = agent.detect_communities()
    
    # Get community statistics
    communities = community_result['communities']
    
    # Analyze community sizes
    large_communities = [c for c in communities if c['size'] >= 5]
    small_communities = [c for c in communities if c['size'] < 5]
    
    # Get centrality for community representatives
    centrality_result = agent.get_centrality_metrics(limit=50)
    pagerank_works = {r['work_id']: r['pagerank_score'] 
                     for r in centrality_result['metrics']['pagerank']['records']}
    
    # Find most central work in each large community
    community_leaders = []
    for community in large_communities:
        max_pagerank = 0
        leader = None
        for work in community['works']:
            work_id = work['work_id']
            pagerank = pagerank_works.get(work_id, 0)
            if pagerank > max_pagerank:
                max_pagerank = pagerank
                leader = work
        
        if leader:
            community_leaders.append({
                'community_id': community['community_id'],
                'leader': leader,
                'pagerank': max_pagerank,
                'community_size': community['size']
            })
    
    return {
        'total_communities': len(communities),
        'large_communities': len(large_communities),
        'small_communities': len(small_communities),
        'community_leaders': community_leaders
    }
```

### 3. Confidence Score Interpretation
```python
def interpret_confidence_scores(results):
    """Interpret confidence scores for related works."""
    
    records = results['results']['comprehensive']['records']
    
    interpretation = []
    for record in records:
        confidence = record['confidence_score']
        title = record['related_work_title']
        
        if confidence >= 0.8:
            strength = "Very Strong"
            description = "Highly related through multiple network measures"
        elif confidence >= 0.6:
            strength = "Strong" 
            description = "Well-connected through several network paths"
        elif confidence >= 0.4:
            strength = "Moderate"
            description = "Some network connections present"
        elif confidence >= 0.2:
            strength = "Weak"
            description = "Limited network connectivity"
        else:
            strength = "Very Weak"
            description = "Minimal network relationship"
        
        interpretation.append({
            'title': title,
            'confidence': confidence,
            'strength': strength,
            'description': description,
            'metrics': {
                'pagerank': record.get('pagerank_score', 0),
                'betweenness': record.get('betweenness_centrality', 0),
                'degree': record.get('degree_centrality', 0),
                'community': record.get('community_id')
            }
        })
    
    return interpretation
```

## Metric Explanations

### Centrality Measures

#### 1. Degree Centrality
- **Range**: 0.0 to 1.0
- **Interpretation**: Higher values = more direct connections
- **Use Case**: Find highly connected works

```python
# Works with degree centrality > 0.1 are highly connected
high_degree_works = [w for w in works if w['degree_centrality'] > 0.1]
```

#### 2. Betweenness Centrality  
- **Range**: 0.0 to 1.0
- **Interpretation**: Higher values = important bridge between other works
- **Use Case**: Find works that connect different research areas

```python
# Works with betweenness > 0.01 are important bridges
bridge_works = [w for w in works if w['betweenness_centrality'] > 0.01]
```

#### 3. Closeness Centrality
- **Range**: 0.0 to 1.0  
- **Interpretation**: Higher values = can reach other works efficiently
- **Use Case**: Find works with good network accessibility

```python
# Works with closeness > 0.5 have good network reach
accessible_works = [w for w in works if w['closeness_centrality'] > 0.5]
```

#### 4. PageRank Score
- **Range**: 0.0 to 1.0 (sum across all nodes = 1.0)
- **Interpretation**: Higher values = more important in network
- **Use Case**: Find most influential works

```python
# Works with PageRank > 0.001 are above average importance
important_works = [w for w in works if w['pagerank_score'] > 0.001]
```

### Confidence Scores

#### Composite Confidence Calculation
```python
confidence = (
    degree_centrality * 0.2 +
    betweenness_centrality * 0.3 +
    closeness_centrality * 0.2 +
    pagerank_score * 0.3
) * community_bonus
```

#### Confidence Interpretation
- **0.8-1.0**: Very Strong relationship
- **0.6-0.8**: Strong relationship  
- **0.4-0.6**: Moderate relationship
- **0.2-0.4**: Weak relationship
- **0.0-0.2**: Very weak relationship

## Integration Examples

### 1. Research Dashboard Integration
```python
class NetworkAnalysisDashboard:
    def __init__(self):
        self.agent = NetworkAnalysisAgent(ConfigManager())
    
    def get_work_network_analysis(self, work_title):
        """Get comprehensive network analysis for a work."""
        result = self.agent.find_related_by_network_analysis(
            title_keyword=work_title,
            analysis_types=["comprehensive", "community"],
            limit=20
        )
        
        return {
            'related_works': result['results']['comprehensive']['records'],
            'community_info': result['results']['community']['records'],
            'metrics_summary': self._summarize_metrics(result)
        }
    
    def _summarize_metrics(self, result):
        """Summarize network metrics."""
        records = result['results']['comprehensive']['records']
        
        if not records:
            return {}
        
        return {
            'avg_confidence': sum(r['confidence_score'] for r in records) / len(records),
            'max_pagerank': max(r['pagerank_score'] for r in records),
            'unique_communities': len(set(r['community_id'] for r in records)),
            'total_related_works': len(records)
        }
```

### 2. Literature Review Assistant
```python
class LiteratureReviewAssistant:
    def __init__(self):
        self.agent = NetworkAnalysisAgent(ConfigManager())
    
    def expand_literature_review(self, seed_works, confidence_threshold=0.5):
        """Expand literature review using network analysis."""
        all_related = []
        
        for seed_work in seed_works:
            result = self.agent.find_related_by_network_analysis(
                title_keyword=seed_work,
                analysis_types=["comprehensive"],
                limit=15
            )
            
            # Filter by confidence threshold
            high_confidence = [
                r for r in result['results']['comprehensive']['records']
                if r['confidence_score'] >= confidence_threshold
            ]
            
            all_related.extend(high_confidence)
        
        # Remove duplicates and sort by confidence
        unique_works = {}
        for work in all_related:
            work_id = work['related_work_id']
            if work_id not in unique_works or work['confidence_score'] > unique_works[work_id]['confidence_score']:
                unique_works[work_id] = work
        
        return sorted(unique_works.values(), key=lambda x: x['confidence_score'], reverse=True)
```

### 3. Research Impact Assessment
```python
class ResearchImpactAnalyzer:
    def __init__(self):
        self.agent = NetworkAnalysisAgent(ConfigManager())
    
    def assess_work_impact(self, work_title):
        """Assess research impact using network centrality."""
        
        # Get centrality metrics
        centrality_result = self.agent.get_centrality_metrics(limit=100)
        
        # Find the work in centrality rankings
        work_metrics = {}
        for metric_type, metric_data in centrality_result['metrics'].items():
            for i, record in enumerate(metric_data['records']):
                if work_title.lower() in record['title'].lower():
                    work_metrics[metric_type] = {
                        'score': record.get(metric_type.split('_')[0] + '_centrality', 
                                          record.get('pagerank_score', 0)),
                        'rank': i + 1,
                        'percentile': ((len(metric_data['records']) - i) / len(metric_data['records'])) * 100
                    }
                    break
        
        # Calculate overall impact score
        impact_score = 0
        if work_metrics:
            weights = {'pagerank': 0.4, 'betweenness_centrality': 0.3, 'degree_centrality': 0.3}
            for metric, weight in weights.items():
                if metric in work_metrics:
                    impact_score += weight * (work_metrics[metric]['percentile'] / 100)
        
        return {
            'impact_score': impact_score,
            'metrics': work_metrics,
            'interpretation': self._interpret_impact(impact_score)
        }
    
    def _interpret_impact(self, score):
        """Interpret impact score."""
        if score >= 0.8:
            return "Very High Impact - Top tier influential work"
        elif score >= 0.6:
            return "High Impact - Significant influence in network"
        elif score >= 0.4:
            return "Moderate Impact - Notable network presence"
        elif score >= 0.2:
            return "Low Impact - Limited network influence"
        else:
            return "Minimal Impact - Peripheral network position"
```

## Performance Considerations

### 1. Graph Projection Management
```python
# The agent automatically manages graph projections
# But you can check projection status:

def check_graph_status(agent):
    """Check if graph projection exists."""
    return agent._graph_created

# Force recreation of graph projection if needed
def recreate_graph_projection(agent):
    """Recreate graph projection with fresh data."""
    # Drop existing projection
    drop_query = "CALL gds.graph.drop($graph_name) YIELD graphName"
    agent.neo4j_tool(drop_query, graph_name=agent.graph_name)
    
    # Reset flag to force recreation
    agent._graph_created = False
    
    # Next analysis will recreate the projection
    return agent.ensure_graph_projection()
```

### 2. Query Optimization
```python
# Use appropriate limits for large networks
result = agent.find_related_by_network_analysis(
    title_keyword="machine learning",
    limit=50  # Adjust based on network size
)

# Focus on specific analysis types for better performance
result = agent.find_related_by_network_analysis(
    title_keyword="deep learning",
    analysis_types=["comprehensive"],  # Only run needed analyses
    limit=20
)
```

## Error Handling

### Common Error Patterns
```python
def safe_network_analysis(title_keyword):
    """Perform network analysis with error handling."""
    try:
        agent = NetworkAnalysisAgent(ConfigManager())
        
        result = agent.find_related_by_network_analysis(
            title_keyword=title_keyword,
            limit=10
        )
        
        if result.get('error'):
            return {
                'status': 'error',
                'message': result['error'],
                'suggestion': 'Check graph projection and database connectivity'
            }
        
        return {'status': 'success', 'data': result}
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'suggestion': 'Verify Neo4j GDS library is installed and accessible'
        }
```

## Best Practices

### 1. Metric Interpretation
- Use confidence scores as primary ranking mechanism
- Consider multiple centrality measures for comprehensive analysis
- Pay attention to community structure for thematic grouping
- Validate high-confidence results with domain expertise

### 2. Performance Optimization
- Use appropriate limits based on network size
- Cache graph projections when possible
- Focus on specific analysis types when performance is critical
- Monitor memory usage for large networks

### 3. Result Validation
- Cross-reference network-based results with content similarity
- Validate community assignments with domain knowledge
- Use confidence thresholds appropriate for your use case
- Consider temporal aspects of research networks

## Conclusion

The network analysis agent provides sophisticated graph-based discovery capabilities using Neo4j's Graph Data Science library. It delivers:

1. **Quantitative Metrics**: Precise numeric measures for all centrality calculations
2. **Confidence Scoring**: Composite scores combining multiple network measures  
3. **Community Detection**: Algorithmic identification of research clusters
4. **Interpretable Results**: Clear numeric thresholds and explanations
5. **Advanced Algorithms**: State-of-the-art graph algorithms (Louvain, PageRank, etc.)

This enables sophisticated GraphRAG applications with network topology-based relationship discovery and quantitative confidence measures.