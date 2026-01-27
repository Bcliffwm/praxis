#!/usr/bin/env python3
"""
Quick test of work-based discovery functionality
"""

from work_based_relationship_agent import WorkBasedRelationshipAgent, ConfigManager

def test_work_discovery():
    try:
        # Initialize agent
        agent = WorkBasedRelationshipAgent(ConfigManager())
        
        print("Testing Work-Based Discovery...")
        print("=" * 40)
        
        # Test 1: Find works by title keyword
        print("\n1. Finding works with 'Collaborative Research' in title:")
        response1 = agent.query("Find works with titles containing 'Collaborative Research'")
        print(f"Response length: {len(str(response1))} characters")
        
        # Test 2: Find related works
        print("\n2. Finding works related to 'Clinical Characteristics':")
        response2 = agent.query("Show me works related to 'Clinical Characteristics' through shared authors")
        print(f"Response length: {len(str(response2))} characters")
        
        # Test 3: Simple work search
        print("\n3. Simple work search:")
        response3 = agent.query("Find 3 works in the database")
        print(f"Response length: {len(str(response3))} characters")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_work_discovery()