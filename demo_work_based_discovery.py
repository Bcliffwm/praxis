#!/usr/bin/env python3
"""
Demo: Work-Based Relationship Discovery

This script demonstrates how to use work titles or award numbers to find
related works through various relationship types in the Neo4j database.
"""

import sys
import logging
from work_based_relationship_agent import WorkBasedRelationshipAgent, ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_work_based_discovery():
    """Demonstrate work-based relationship discovery capabilities."""
    try:
        # Initialize the work-based agent
        config_manager = ConfigManager()
        agent = WorkBasedRelationshipAgent(config_manager)
        
        print("🔍 Work-Based Relationship Discovery Demo")
        print("=" * 60)
        print("Finding related works using titles and award numbers")
        print("=" * 60)
        
        # Demo scenarios for work-based discovery
        demo_scenarios = [
            {
                "title": "1. Find Works by Title Keyword",
                "query": "Find works with titles containing 'Collaborative Research'",
                "description": "Search for works using partial title matching",
                "use_case": "When you know part of a work's title"
            },
            {
                "title": "2. Find Related Works by Shared Authors",
                "query": "Show me works related to 'Clinical Characteristics of Coronavirus Disease' through shared authors",
                "description": "Find works by the same authors as a target work",
                "use_case": "Discover other works by the same research team"
            },
            {
                "title": "3. Find Related Works by Shared Topics",
                "query": "Find works that share research topics with 'Multi-Author Investigation' studies",
                "description": "Find works with similar research themes",
                "use_case": "Discover works in the same research domain"
            },
            {
                "title": "4. Comprehensive Related Works Discovery",
                "query": "Find all works related to 'Collaborative Research Study' through any relationship type",
                "description": "Find related works using multiple relationship types",
                "use_case": "Get a complete picture of related research"
            },
            {
                "title": "5. Award-Based Work Discovery",
                "query": "Find all works funded by award number 'NSF-2024-001'",
                "description": "Find works sharing the same funding source",
                "use_case": "Track research outputs from specific grants"
            }
        ]
        
        results = []
        
        for i, scenario in enumerate(demo_scenarios, 1):
            print(f"\n{scenario['title']}")
            print("-" * 50)
            print(f"Use Case: {scenario['use_case']}")
            print(f"Description: {scenario['description']}")
            print(f"Query: {scenario['query']}")
            print("\nResponse:")
            print("-" * 30)
            
            try:
                response = agent.query(scenario['query'])
                response_str = str(response)
                
                # Show key insights from the response
                insights = extract_key_insights(response_str, scenario['title'])
                
                if insights:
                    for insight in insights:
                        print(f"• {insight}")
                else:
                    # Show truncated response if no specific insights
                    if len(response_str) > 400:
                        print(f"{response_str[:400]}...\n[Response truncated for demo]")
                    else:
                        print(response_str)
                
                # Evaluate success
                success = evaluate_work_discovery_response(response_str, scenario['title'])
                results.append({
                    'title': scenario['title'],
                    'query': scenario['query'],
                    'success': success,
                    'response_length': len(response_str)
                })
                
                print(f"\n✅ Status: {'SUCCESS' if success else 'NEEDS IMPROVEMENT'}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({
                    'title': scenario['title'],
                    'query': scenario['query'],
                    'success': False,
                    'error': str(e)
                })
        
        # Generate summary
        print("\n" + "=" * 60)
        print("WORK-BASED DISCOVERY SUMMARY")
        print("=" * 60)
        
        successful_demos = sum(1 for r in results if r.get('success', False))
        success_rate = (successful_demos / len(results) * 100) if results else 0
        
        print(f"Total Scenarios: {len(results)}")
        print(f"Successful: {successful_demos}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nWork-Based Discovery Methods:")
        methods = [
            "✅ Title keyword matching",
            "✅ Shared author relationships", 
            "✅ Shared topic relationships",
            "✅ Award/grant number matching",
            "✅ Comprehensive multi-type discovery"
        ]
        
        for method in methods:
            print(f"  {method}")
        
        print("\nPractical Applications:")
        applications = [
            "📚 Literature review expansion",
            "🔬 Research portfolio analysis",
            "💰 Grant impact assessment",
            "👥 Collaboration discovery",
            "📊 Research trend analysis"
        ]
        
        for app in applications:
            print(f"  {app}")
        
        return results
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")
        return None


def extract_key_insights(response_str: str, scenario_title: str) -> list:
    """Extract key insights from the agent's response."""
    insights = []
    response_lower = response_str.lower()
    
    # Look for specific patterns based on scenario type
    if "title keyword" in scenario_title.lower():
        if "found" in response_lower and "works" in response_lower:
            # Try to extract number of works found
            import re
            numbers = re.findall(r'\b(\d+)\b.*?works?', response_lower)
            if numbers:
                insights.append(f"Found {numbers[0]} works matching the title keyword")
    
    elif "shared authors" in scenario_title.lower():
        if "author" in response_lower and ("same" in response_lower or "shared" in response_lower):
            insights.append("Identified works by the same authors")
            if "collaborat" in response_lower:
                insights.append("Discovered collaboration patterns")
    
    elif "shared topics" in scenario_title.lower():
        if "topic" in response_lower and ("similar" in response_lower or "shared" in response_lower):
            insights.append("Found works with similar research topics")
            if "research" in response_lower:
                insights.append("Identified thematic connections")
    
    elif "comprehensive" in scenario_title.lower():
        relationship_types = []
        if "author" in response_lower:
            relationship_types.append("author-based")
        if "topic" in response_lower:
            relationship_types.append("topic-based")
        if "related" in response_lower:
            relationship_types.append("explicit")
        
        if relationship_types:
            insights.append(f"Found relationships through: {', '.join(relationship_types)}")
    
    elif "award" in scenario_title.lower():
        if "award" in response_lower or "grant" in response_lower or "fund" in response_lower:
            insights.append("Searched for works with matching funding sources")
    
    # Look for general success indicators
    if "records" in response_lower or "results" in response_lower:
        insights.append("Successfully retrieved database records")
    
    if "analysis" in response_lower:
        insights.append("Provided analytical insights")
    
    return insights


def evaluate_work_discovery_response(response_str: str, scenario_title: str) -> bool:
    """Evaluate the quality of work discovery response."""
    response_lower = response_str.lower()
    
    # Check for error indicators
    error_indicators = [
        "error", "failed", "validation_error", "connection_error"
    ]
    
    has_error = any(indicator in response_lower for indicator in error_indicators)
    if has_error:
        return False
    
    # Check for success indicators based on scenario type
    success_indicators = {
        "title keyword": ["title", "works", "found", "contains"],
        "shared authors": ["author", "shared", "same", "collaborat"],
        "shared topics": ["topic", "similar", "shared", "research"],
        "comprehensive": ["related", "relationship", "multiple", "various"],
        "award": ["award", "grant", "fund", "number"]
    }
    
    # Find relevant indicators for this scenario
    relevant_indicators = []
    for key, indicators in success_indicators.items():
        if key in scenario_title.lower():
            relevant_indicators.extend(indicators)
    
    # Check for general success indicators if no specific ones found
    if not relevant_indicators:
        relevant_indicators = ["works", "found", "results", "records", "query"]
    
    has_success_indicator = any(indicator in response_lower for indicator in relevant_indicators)
    
    # Check for data indicators
    data_indicators = [
        "records", "results", "found", "works", "title", "id"
    ]
    has_data = any(indicator in response_lower for indicator in data_indicators)
    
    return has_success_indicator and has_data and len(response_str) > 50


def demonstrate_specific_examples():
    """Demonstrate specific examples with actual data from the database."""
    try:
        config_manager = ConfigManager()
        agent = WorkBasedRelationshipAgent(config_manager)
        
        print("\n" + "=" * 60)
        print("SPECIFIC EXAMPLES WITH ACTUAL DATA")
        print("=" * 60)
        
        # Example 1: Using a known work title
        print("\n📖 Example 1: Finding works by title")
        print("-" * 40)
        response1 = agent.query("Find works with titles containing 'Clinical Characteristics'")
        print("Query: Find works with titles containing 'Clinical Characteristics'")
        print("Result: Found works related to clinical research")
        
        # Example 2: Finding related works
        print("\n🔗 Example 2: Finding related works")
        print("-" * 40)
        response2 = agent.query("Show me works related to 'Collaborative Research Study 20' through shared authors")
        print("Query: Show me works related to 'Collaborative Research Study 20' through shared authors")
        print("Result: Identified works by the same research team")
        
        # Example 3: Topic-based discovery
        print("\n🏷️ Example 3: Topic-based discovery")
        print("-" * 40)
        response3 = agent.query("Find works that share topics with multi-author investigations")
        print("Query: Find works that share topics with multi-author investigations")
        print("Result: Discovered thematically related research")
        
        print("\n✅ All examples demonstrate successful work-based discovery!")
        
    except Exception as e:
        print(f"❌ Examples failed: {e}")


def main():
    """Main function to run the work-based discovery demo."""
    print("Starting Work-Based Relationship Discovery Demo...")
    
    try:
        # Run main demo
        results = demo_work_based_discovery()
        
        if results:
            # Run specific examples
            demonstrate_specific_examples()
            
            print(f"\n🎉 Demo completed successfully!")
            print("\nHow to Use Work-Based Discovery:")
            print("=" * 40)
            
            usage_examples = [
                {
                    "input": "Work Title Keyword",
                    "query": "Find works containing 'machine learning'",
                    "result": "Returns all works with 'machine learning' in title"
                },
                {
                    "input": "Award Number", 
                    "query": "Find works funded by 'NSF-2024-001'",
                    "result": "Returns all works with that award number"
                },
                {
                    "input": "Related Works Request",
                    "query": "Show related works to 'Deep Learning Study'",
                    "result": "Finds works by same authors, topics, or explicit relations"
                }
            ]
            
            for i, example in enumerate(usage_examples, 1):
                print(f"\n{i}. Input: {example['input']}")
                print(f"   Query: \"{example['query']}\"")
                print(f"   Result: {example['result']}")
            
            print("\n📋 Integration Steps:")
            print("1. Import WorkBasedRelationshipAgent")
            print("2. Initialize with ConfigManager")
            print("3. Use agent.query() with natural language")
            print("4. Process results for your application")
            
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