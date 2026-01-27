#!/usr/bin/env python3
"""
Demo: Network Analysis with Neo4j Graph Data Science

Demonstrates advanced network analysis capabilities including:
- Centrality measures (degree, betweenness, closeness, PageRank)
- Community detection using Louvain algorithm
- Shortest path analysis
- Confidence scores and numeric metrics
"""

import sys
import json
import logging
from network_analysis_agent import NetworkAnalysisAgent, ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_network_analysis():
    """Demonstrate comprehensive network analysis capabilities."""
    try:
        # Initialize the network analysis agent
        config_manager = ConfigManager()
        agent = NetworkAnalysisAgent(config_manager)
        
        print("🕸️  Network Analysis with Neo4j Graph Data Science")
        print("=" * 70)
        print("Finding related works using advanced graph algorithms and centrality measures")
        print("=" * 70)
        
        # Demo scenarios for network analysis
        demo_scenarios = [
            {
                "title": "1. Comprehensive Network Analysis",
                "description": "Find related works using multiple centrality measures and community detection",
                "method": "comprehensive_analysis",
                "params": {"title_keyword": "Collaborative Research", "limit": 5}
            },
            {
                "title": "2. Centrality Metrics Analysis", 
                "description": "Get centrality scores (PageRank, betweenness, closeness, degree) for top works",
                "method": "centrality_metrics",
                "params": {"limit": 10}
            },
            {
                "title": "3. Community Detection",
                "description": "Detect research communities using Louvain algorithm",
                "method": "community_detection", 
                "params": {}
            },
            {
                "title": "4. Network-Based Related Works",
                "description": "Find works related through network topology with confidence scores",
                "method": "network_related_works",
                "params": {"title_keyword": "Clinical Characteristics", "limit": 5}
            }
        ]
        
        results = {}
        
        for scenario in demo_scenarios:
            print(f"\n{scenario['title']}")
            print("-" * 60)
            print(f"Description: {scenario['description']}")
            print("\nExecuting analysis...")
            
            try:
                if scenario['method'] == "comprehensive_analysis":
                    result = agent.find_related_by_network_analysis(**scenario['params'])
                elif scenario['method'] == "centrality_metrics":
                    result = agent.get_centrality_metrics(**scenario['params'])
                elif scenario['method'] == "community_detection":
                    result = agent.detect_communities()
                elif scenario['method'] == "network_related_works":
                    result = agent.find_related_by_network_analysis(
                        analysis_types=["comprehensive", "community"], 
                        **scenario['params']
                    )
                
                # Process and display results
                display_results(scenario['title'], result)
                results[scenario['method']] = result
                
            except Exception as e:
                print(f"❌ Error: {e}")
                results[scenario['method']] = {"error": str(e)}
        
        # Generate comprehensive summary
        generate_network_summary(results)
        
        return results
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
        return None


def display_results(title: str, result: dict) -> None:
    """Display network analysis results with formatted metrics."""
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return
    
    print("✅ Analysis completed successfully!")
    
    if "centrality_metrics" in title.lower():
        display_centrality_results(result)
    elif "community" in title.lower():
        display_community_results(result)
    elif "comprehensive" in title.lower() or "network-based" in title.lower():
        display_network_analysis_results(result)
    else:
        print(f"📊 Result summary: {len(result.get('records', []))} items found")


def display_centrality_results(result: dict) -> None:
    """Display centrality metrics with numeric values."""
    print("\n📊 Centrality Metrics:")
    
    metrics = result.get('metrics', {})
    
    for metric_type, metric_data in metrics.items():
        if metric_data.get('error'):
            print(f"  ❌ {metric_type}: {metric_data['error']}")
            continue
        
        records = metric_data.get('records', [])
        if not records:
            print(f"  ⚠️  {metric_type}: No data")
            continue
        
        print(f"\n  🎯 {metric_type.replace('_', ' ').title()}:")
        
        for i, record in enumerate(records[:3], 1):  # Show top 3
            work_title = record.get('title', 'Unknown')[:50]
            score = record.get(metric_type.split('_')[0] + '_centrality', 
                              record.get('pagerank_score', 0))
            
            print(f"    {i}. {work_title}...")
            print(f"       Score: {score:.6f}")


def display_community_results(result: dict) -> None:
    """Display community detection results."""
    print("\n🏘️  Community Structure:")
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return
    
    communities = result.get('communities', [])
    total_communities = result.get('total_communities', 0)
    total_works = result.get('total_works', 0)
    
    print(f"  📈 Total Communities: {total_communities}")
    print(f"  📚 Total Works: {total_works}")
    print(f"  🏆 Largest Community: {result.get('largest_community_size', 0)} works")
    
    print(f"\n  🔍 Top Communities:")
    for i, community in enumerate(communities[:3], 1):
        print(f"    Community {community['community_id']}: {community['size']} works")
        for work in community['works'][:2]:  # Show first 2 works
            print(f"      • {work['title'][:40]}...")


def display_network_analysis_results(result: dict) -> None:
    """Display comprehensive network analysis results."""
    print("\n🕸️  Network Analysis Results:")
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return
    
    analysis_results = result.get('results', {})
    
    for analysis_type, analysis_data in analysis_results.items():
        if analysis_data.get('error'):
            print(f"  ❌ {analysis_type}: {analysis_data['error']}")
            continue
        
        records = analysis_data.get('records', [])
        if not records:
            print(f"  ⚠️  {analysis_type}: No related works found")
            continue
        
        print(f"\n  🎯 {analysis_type.replace('_', ' ').title()} Analysis:")
        print(f"     Found {len(records)} related works")
        
        # Show top results with metrics
        for i, record in enumerate(records[:3], 1):
            work_title = record.get('related_work_title', record.get('title', 'Unknown'))[:45]
            confidence = record.get('confidence_score', 0)
            
            print(f"    {i}. {work_title}...")
            print(f"       Confidence Score: {confidence:.4f}")
            
            # Show specific metrics if available
            if 'degree_centrality' in record:
                print(f"       Degree Centrality: {record.get('degree_centrality', 0):.6f}")
            if 'betweenness_centrality' in record:
                print(f"       Betweenness Centrality: {record.get('betweenness_centrality', 0):.6f}")
            if 'pagerank_score' in record:
                print(f"       PageRank Score: {record.get('pagerank_score', 0):.6f}")
            if 'community_id' in record:
                print(f"       Community ID: {record.get('community_id')}")


def generate_network_summary(results: dict) -> None:
    """Generate comprehensive summary of network analysis results."""
    print("\n" + "=" * 70)
    print("NETWORK ANALYSIS SUMMARY")
    print("=" * 70)
    
    # Count successful analyses
    successful_analyses = sum(1 for result in results.values() if not result.get('error'))
    total_analyses = len(results)
    success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
    
    print(f"📊 Analysis Success Rate: {success_rate:.1f}% ({successful_analyses}/{total_analyses})")
    
    # Network metrics summary
    print(f"\n🕸️  Network Metrics Available:")
    metrics_available = [
        "✅ Degree Centrality (connectivity measure)",
        "✅ Betweenness Centrality (bridge node identification)", 
        "✅ Closeness Centrality (optimal path measure)",
        "✅ PageRank Score (importance ranking)",
        "✅ Community Detection (Louvain algorithm)",
        "✅ Confidence Scoring (composite metrics)"
    ]
    
    for metric in metrics_available:
        print(f"  {metric}")
    
    # Key insights
    print(f"\n🔍 Key Insights:")
    insights = []
    
    # Community insights
    if 'community_detection' in results and not results['community_detection'].get('error'):
        community_data = results['community_detection']
        total_communities = community_data.get('total_communities', 0)
        largest_community = community_data.get('largest_community_size', 0)
        insights.append(f"Detected {total_communities} research communities")
        insights.append(f"Largest community contains {largest_community} works")
    
    # Centrality insights
    if 'centrality_metrics' in results and not results['centrality_metrics'].get('error'):
        insights.append("Successfully calculated multiple centrality measures")
        insights.append("Identified most influential works in the network")
    
    # Network analysis insights
    if 'comprehensive_analysis' in results and not results['comprehensive_analysis'].get('error'):
        insights.append("Composite confidence scores calculated from multiple metrics")
        insights.append("Network topology used for relationship discovery")
    
    for insight in insights:
        print(f"  • {insight}")
    
    # Practical applications
    print(f"\n🎯 Practical Applications Enabled:")
    applications = [
        "📚 Literature review with network-based relevance ranking",
        "🔬 Research impact assessment using centrality measures",
        "👥 Collaboration network analysis and community mapping",
        "📊 Research portfolio analysis with quantitative metrics",
        "🎯 Targeted research discovery using graph algorithms",
        "📈 Influence tracking through PageRank and betweenness centrality"
    ]
    
    for app in applications:
        print(f"  {app}")


def demonstrate_specific_metrics():
    """Demonstrate specific network metrics with actual values."""
    try:
        config_manager = ConfigManager()
        agent = NetworkAnalysisAgent(config_manager)
        
        print("\n" + "=" * 70)
        print("SPECIFIC NETWORK METRICS DEMONSTRATION")
        print("=" * 70)
        
        # Example 1: Get centrality metrics
        print("\n📊 Example 1: Centrality Metrics for Top Works")
        print("-" * 50)
        
        centrality_result = agent.get_centrality_metrics(limit=5)
        if not centrality_result.get('error'):
            print("✅ Successfully calculated centrality metrics")
            print("   Metrics include: PageRank, Degree, Betweenness, Closeness")
        else:
            print(f"❌ Error: {centrality_result['error']}")
        
        # Example 2: Community detection
        print("\n🏘️  Example 2: Community Detection")
        print("-" * 50)
        
        community_result = agent.detect_communities()
        if not community_result.get('error'):
            communities = community_result.get('total_communities', 0)
            works = community_result.get('total_works', 0)
            print(f"✅ Detected {communities} communities across {works} works")
            print("   Algorithm: Louvain community detection")
        else:
            print(f"❌ Error: {community_result['error']}")
        
        # Example 3: Network-based related works
        print("\n🕸️  Example 3: Network-Based Related Works Discovery")
        print("-" * 50)
        
        network_result = agent.find_related_by_network_analysis(
            title_keyword="Collaborative Research",
            analysis_types=["comprehensive"],
            limit=3
        )
        
        if not network_result.get('error'):
            print("✅ Found related works using network topology")
            print("   Metrics: Composite confidence scores from multiple centrality measures")
        else:
            print(f"❌ Error: {network_result['error']}")
        
        print("\n🎉 Network analysis capabilities demonstrated!")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")


def main():
    """Main function to run the network analysis demo."""
    print("Starting Network Analysis Demo with Neo4j Graph Data Science...")
    
    try:
        # Run main demo
        results = demo_network_analysis()
        
        if results:
            # Run specific metrics demonstration
            demonstrate_specific_metrics()
            
            print(f"\n🎉 Demo completed successfully!")
            print("\nHow to Use Network Analysis:")
            print("=" * 50)
            
            usage_examples = [
                {
                    "input": "Work Title",
                    "method": "find_related_by_network_analysis(title_keyword='title')",
                    "output": "Related works with confidence scores and centrality metrics"
                },
                {
                    "input": "Centrality Analysis",
                    "method": "get_centrality_metrics(limit=10)",
                    "output": "PageRank, degree, betweenness, closeness centrality scores"
                },
                {
                    "input": "Community Detection",
                    "method": "detect_communities()",
                    "output": "Research communities with size and member statistics"
                }
            ]
            
            for i, example in enumerate(usage_examples, 1):
                print(f"\n{i}. Input: {example['input']}")
                print(f"   Method: {example['method']}")
                print(f"   Output: {example['output']}")
            
            print("\n📋 Key Features:")
            print("✅ Neo4j Graph Data Science integration")
            print("✅ Multiple centrality measures")
            print("✅ Community detection algorithms")
            print("✅ Confidence scoring with numeric metrics")
            print("✅ Interpretable results with quantitative measures")
            
        else:
            print("❌ Demo failed to complete")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()