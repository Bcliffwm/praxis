#!/usr/bin/env python3
"""
Fix Relationship Direction and Create Co-authorship Patterns

This script analyzes the current relationship direction and creates proper
co-authorship relationships for testing the agent's inference capabilities.
"""

import sys
import random
import logging
from research_query_agent import ConfigManager, Neo4jClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_current_relationships():
    """Analyze the current relationship patterns in the database."""
    try:
        config_manager = ConfigManager()
        neo4j_config = config_manager.get_neo4j_config()
        
        client = Neo4jClient(
            uri=neo4j_config['uri'],
            auth=neo4j_config['auth'],
            database=neo4j_config['database']
        )
        
        print("Analyzing Current Relationship Patterns")
        print("=" * 50)
        
        # Check the direction of WORK_AUTHORED_BY relationships
        direction_queries = [
            ("Author -> Work", "MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work) RETURN count(*) as count"),
            ("Work -> Author", "MATCH (w:Work)-[:WORK_AUTHORED_BY]->(a:Author) RETURN count(*) as count"),
            ("Author <- Work", "MATCH (a:Author)<-[:WORK_AUTHORED_BY]-(w:Work) RETURN count(*) as count"),
            ("Work <- Author", "MATCH (w:Work)<-[:WORK_AUTHORED_BY]-(a:Author) RETURN count(*) as count")
        ]
        
        print("\n1. Relationship Direction Analysis:")
        print("-" * 30)
        
        for direction, query in direction_queries:
            try:
                result = client.run_cypher(query)
                count = result[0]['count'] if result else 0
                if count > 0:
                    print(f"  {direction}: {count:,} relationships")
            except Exception as e:
                print(f"  {direction}: Error - {e}")
        
        # Check how many authors per work
        authors_per_work_query = """
        MATCH (w:Work)
        OPTIONAL MATCH (w)<-[:WORK_AUTHORED_BY]-(a:Author)
        WITH w, COUNT(a) as author_count
        RETURN author_count, COUNT(w) as work_count
        ORDER BY author_count
        """
        
        print("\n2. Authors per Work Distribution:")
        print("-" * 30)
        
        try:
            result = client.run_cypher(authors_per_work_query)
            for record in result:
                author_count = record['author_count']
                work_count = record['work_count']
                print(f"  {author_count} authors: {work_count:,} works")
        except Exception as e:
            print(f"  Error analyzing authors per work: {e}")
        
        # Check works per author
        works_per_author_query = """
        MATCH (a:Author)
        OPTIONAL MATCH (a)-[:WORK_AUTHORED_BY]->(w:Work)
        WITH a, COUNT(w) as work_count
        RETURN work_count, COUNT(a) as author_count
        ORDER BY work_count
        LIMIT 10
        """
        
        print("\n3. Works per Author Distribution (Top 10):")
        print("-" * 30)
        
        try:
            result = client.run_cypher(works_per_author_query)
            for record in result:
                work_count = record['work_count']
                author_count = record['author_count']
                print(f"  {work_count} works: {author_count:,} authors")
        except Exception as e:
            print(f"  Error analyzing works per author: {e}")
        
        # Sample some actual relationships
        print("\n4. Sample Relationships:")
        print("-" * 30)
        
        sample_query = """
        MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work)
        RETURN a.name as author_name, w.title as work_title
        LIMIT 5
        """
        
        try:
            result = client.run_cypher(sample_query)
            if result:
                for i, record in enumerate(result, 1):
                    author = record.get('author_name', 'Unknown')
                    work = record.get('work_title', 'Unknown')
                    print(f"  {i}. {author} -> {work[:50]}...")
            else:
                print("  No Author -> Work relationships found")
        except Exception as e:
            print(f"  Error getting sample relationships: {e}")
        
        # Try the reverse direction
        reverse_sample_query = """
        MATCH (w:Work)<-[:WORK_AUTHORED_BY]-(a:Author)
        RETURN a.name as author_name, w.title as work_title
        LIMIT 5
        """
        
        try:
            result = client.run_cypher(reverse_sample_query)
            if result:
                print("\n  Reverse direction (Work <- Author):")
                for i, record in enumerate(result, 1):
                    author = record.get('author_name', 'Unknown')
                    work = record.get('work_title', 'Unknown')
                    print(f"  {i}. {work[:50]}... <- {author}")
        except Exception as e:
            print(f"  Error getting reverse sample relationships: {e}")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to analyze relationships: {e}")
        return False


def create_multi_author_works(num_works=50):
    """Create works with multiple authors to enable co-authorship testing."""
    try:
        config_manager = ConfigManager()
        neo4j_config = config_manager.get_neo4j_config()
        
        client = Neo4jClient(
            uri=neo4j_config['uri'],
            auth=neo4j_config['auth'],
            database=neo4j_config['database']
        )
        
        print(f"\nCreating {num_works} multi-author works...")
        print("=" * 50)
        
        # Get a sample of authors
        authors_query = """
        MATCH (a:Author)
        RETURN a.id as author_id, a.name as author_name
        LIMIT 500
        """
        
        authors_result = client.run_cypher(authors_query)
        if len(authors_result) < 10:
            print("❌ Not enough authors to create multi-author works")
            return False
        
        print(f"Using {len(authors_result)} authors for multi-author work creation")
        
        # Get some topics for the new works
        topics_query = """
        MATCH (t:Topic)
        RETURN t.id as topic_id, t.topic_name as topic_name
        LIMIT 100
        """
        
        topics_result = client.run_cypher(topics_query)
        
        created_works = 0
        created_relationships = 0
        
        for i in range(num_works):
            # Create a new work
            work_id = f"W_MULTI_{i+1:04d}"
            work_title = f"Collaborative Research Study {i+1}: Multi-Author Investigation"
            
            # Select 2-5 random authors for this work
            num_authors = random.randint(2, 5)
            selected_authors = random.sample(authors_result, num_authors)
            
            # Create the work
            create_work_query = """
            CREATE (w:Work {
                id: $work_id,
                title: $work_title,
                type: 'multi-author-research',
                publication_date: date('2024-01-01')
            })
            """
            
            try:
                client.run_cypher(create_work_query, {
                    'work_id': work_id,
                    'work_title': work_title
                })
                created_works += 1
                
                # Create authorship relationships for each selected author
                for author in selected_authors:
                    author_id = author['author_id']
                    
                    # Create the relationship (Author -> Work direction based on existing pattern)
                    create_auth_query = """
                    MATCH (a:Author {id: $author_id}), (w:Work {id: $work_id})
                    CREATE (a)-[:WORK_AUTHORED_BY]->(w)
                    """
                    
                    client.run_cypher(create_auth_query, {
                        'author_id': author_id,
                        'work_id': work_id
                    })
                    created_relationships += 1
                
                # Optionally link to a random topic
                if topics_result and random.random() < 0.7:  # 70% chance of having a topic
                    selected_topic = random.choice(topics_result)
                    
                    link_topic_query = """
                    MATCH (w:Work {id: $work_id}), (t:Topic {id: $topic_id})
                    CREATE (w)-[:WORK_HAS_TOPIC]->(t)
                    """
                    
                    try:
                        client.run_cypher(link_topic_query, {
                            'work_id': work_id,
                            'topic_id': selected_topic['topic_id']
                        })
                    except Exception as e:
                        logger.warning(f"Failed to link topic to work {work_id}: {e}")
                
                if (i + 1) % 10 == 0:
                    print(f"  Created {i + 1}/{num_works} multi-author works...")
            
            except Exception as e:
                logger.warning(f"Failed to create multi-author work {work_id}: {e}")
        
        print(f"\n✅ Successfully created:")
        print(f"   - {created_works} multi-author works")
        print(f"   - {created_relationships} authorship relationships")
        
        # Verify co-authorship patterns now exist
        print("\nVerifying co-authorship patterns...")
        
        # Try both directions to see which one works
        coauth_queries = [
            ("Author -> Work <- Author", """
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE a1 <> a2
                RETURN count(*) as count
            """),
            ("Author <- Work -> Author", """
                MATCH (a1:Author)<-[:WORK_AUTHORED_BY]-(w:Work)-[:WORK_AUTHORED_BY]->(a2:Author)
                WHERE a1 <> a2
                RETURN count(*) as count
            """)
        ]
        
        for pattern, query in coauth_queries:
            try:
                result = client.run_cypher(query)
                count = result[0]['count'] if result else 0
                print(f"  {pattern}: {count:,} co-authorship instances")
                
                if count > 0:
                    # Get sample co-authorships
                    sample_query = query.replace("RETURN count(*) as count", 
                                                "RETURN a1.name as author1, a2.name as author2, w.title as work_title LIMIT 3")
                    
                    sample_result = client.run_cypher(sample_query)
                    if sample_result:
                        print(f"    Sample {pattern} collaborations:")
                        for j, record in enumerate(sample_result, 1):
                            print(f"      {j}. {record.get('author1', 'Unknown')} & {record.get('author2', 'Unknown')}")
                            print(f"         Work: {record.get('work_title', 'Unknown')[:50]}...")
            
            except Exception as e:
                print(f"  Error checking {pattern}: {e}")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create multi-author works: {e}")
        return False


def test_coauthorship_queries():
    """Test various co-authorship query patterns to find what works."""
    try:
        config_manager = ConfigManager()
        neo4j_config = config_manager.get_neo4j_config()
        
        client = Neo4jClient(
            uri=neo4j_config['uri'],
            auth=neo4j_config['auth'],
            database=neo4j_config['database']
        )
        
        print("\nTesting Co-authorship Query Patterns")
        print("=" * 50)
        
        test_queries = [
            ("Standard Pattern (Author -> Work <- Author)", """
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE a1 <> a2
                RETURN a1.name as author1, a2.name as author2, w.title as work_title
                LIMIT 5
            """),
            ("Reverse Pattern (Author <- Work -> Author)", """
                MATCH (a1:Author)<-[:WORK_AUTHORED_BY]-(w:Work)-[:WORK_AUTHORED_BY]->(a2:Author)
                WHERE a1 <> a2
                RETURN a1.name as author1, a2.name as author2, w.title as work_title
                LIMIT 5
            """),
            ("Bidirectional Pattern", """
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]-(w:Work)-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE a1 <> a2
                RETURN a1.name as author1, a2.name as author2, w.title as work_title
                LIMIT 5
            """)
        ]
        
        working_patterns = []
        
        for pattern_name, query in test_queries:
            print(f"\n{pattern_name}:")
            print("-" * 30)
            
            try:
                result = client.run_cypher(query)
                if result:
                    print(f"  ✅ Found {len(result)} co-authorship instances")
                    working_patterns.append((pattern_name, query))
                    
                    for i, record in enumerate(result, 1):
                        author1 = record.get('author1', 'Unknown')
                        author2 = record.get('author2', 'Unknown')
                        work_title = record.get('work_title', 'Unknown')
                        print(f"    {i}. {author1} & {author2}")
                        print(f"       Work: {work_title[:50]}...")
                else:
                    print("  ❌ No co-authorship instances found")
            
            except Exception as e:
                print(f"  ❌ Query failed: {e}")
        
        client.close()
        
        print(f"\n📊 Summary: {len(working_patterns)} working patterns found")
        
        if working_patterns:
            print("\n✅ Working patterns for agent testing:")
            for pattern_name, _ in working_patterns:
                print(f"  - {pattern_name}")
            return True
        else:
            print("\n❌ No working co-authorship patterns found")
            return False
        
    except Exception as e:
        logger.error(f"Failed to test co-authorship queries: {e}")
        return False


def main():
    """Main function to fix relationships and enable co-authorship testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix relationship direction and create co-authorship patterns")
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze current relationships without creating new ones')
    parser.add_argument('--multi-works', type=int, default=50,
                       help='Number of multi-author works to create (default: 50)')
    
    args = parser.parse_args()
    
    print("Relationship Direction Fixer and Co-authorship Creator")
    print("=" * 60)
    
    try:
        # Step 1: Analyze current relationships
        print("Step 1: Analyzing current relationship patterns...")
        if not analyze_current_relationships():
            print("❌ Failed to analyze current relationships")
            return
        
        if args.analyze_only:
            print("\n✅ Analysis complete (analyze-only mode)")
            return
        
        # Step 2: Create multi-author works
        print("\nStep 2: Creating multi-author works...")
        if not create_multi_author_works(args.multi_works):
            print("❌ Failed to create multi-author works")
            return
        
        # Step 3: Test co-authorship query patterns
        print("\nStep 3: Testing co-authorship query patterns...")
        if test_coauthorship_queries():
            print("\n🎉 Success! Co-authorship patterns are now available for testing")
            print("\nNext steps:")
            print("1. Run 'python check_database_structure.py' to verify the changes")
            print("2. Run 'python run_relationship_tests.py' to test the agent")
        else:
            print("\n⚠️  Co-authorship patterns may need further investigation")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()