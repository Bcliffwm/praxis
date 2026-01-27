#!/usr/bin/env python3
"""
Check Database Structure

This script examines the current Neo4j database structure to understand
what data and relationships are available for author relationship inference.
"""

import sys
import logging
from research_query_agent import ConfigManager, Neo4jClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_database_structure():
    """Check the current database structure and relationships."""
    try:
        # Initialize configuration and client
        config_manager = ConfigManager()
        neo4j_config = config_manager.get_neo4j_config()
        
        client = Neo4jClient(
            uri=neo4j_config['uri'],
            auth=neo4j_config['auth'],
            database=neo4j_config['database']
        )
        
        print("Neo4j Database Structure Analysis")
        print("=" * 50)
        
        # Check node types and counts
        print("\n1. Node Types and Counts:")
        print("-" * 30)
        
        node_queries = [
            ("Authors", "MATCH (n:Author) RETURN count(n) as count"),
            ("Works", "MATCH (n:Work) RETURN count(n) as count"),
            ("Topics", "MATCH (n:Topic) RETURN count(n) as count")
        ]
        
        for label, query in node_queries:
            try:
                result = client.run_cypher(query)
                count = result[0]['count'] if result else 0
                print(f"  {label}: {count:,}")
            except Exception as e:
                print(f"  {label}: Error - {e}")
        
        # Check relationship types and counts
        print("\n2. Relationship Types and Counts:")
        print("-" * 30)
        
        rel_queries = [
            ("WORK_AUTHORED_BY", "MATCH ()-[r:WORK_AUTHORED_BY]->() RETURN count(r) as count"),
            ("WORK_HAS_TOPIC", "MATCH ()-[r:WORK_HAS_TOPIC]->() RETURN count(r) as count"),
            ("RELATED_TO", "MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count")
        ]
        
        for rel_type, query in rel_queries:
            try:
                result = client.run_cypher(query)
                count = result[0]['count'] if result else 0
                print(f"  {rel_type}: {count:,}")
            except Exception as e:
                print(f"  {rel_type}: Error - {e}")
        
        # Check for potential co-authorship relationships
        print("\n3. Co-authorship Analysis:")
        print("-" * 30)
        
        coauth_query = """
        MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
        WHERE a1 <> a2
        RETURN count(*) as coauthorship_instances
        """
        
        try:
            result = client.run_cypher(coauth_query)
            count = result[0]['coauthorship_instances'] if result else 0
            print(f"  Co-authorship instances: {count:,}")
            
            if count > 0:
                # Get sample co-authorships
                sample_query = """
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE a1 <> a2
                RETURN a1.name as author1, a2.name as author2, w.title as work_title
                LIMIT 5
                """
                
                sample_result = client.run_cypher(sample_query)
                if sample_result:
                    print("\n  Sample Co-authorships:")
                    for i, record in enumerate(sample_result, 1):
                        print(f"    {i}. {record.get('author1', 'Unknown')} & {record.get('author2', 'Unknown')}")
                        print(f"       Work: {record.get('work_title', 'Unknown')[:60]}...")
            else:
                print("  ⚠️  No co-authorship relationships found!")
                print("     This may indicate missing WORK_AUTHORED_BY relationships")
        
        except Exception as e:
            print(f"  Error analyzing co-authorship: {e}")
        
        # Check author properties
        print("\n4. Author Node Properties:")
        print("-" * 30)
        
        author_props_query = """
        MATCH (a:Author)
        RETURN keys(a) as properties
        LIMIT 1
        """
        
        try:
            result = client.run_cypher(author_props_query)
            if result:
                properties = result[0].get('properties', [])
                print(f"  Available properties: {', '.join(properties)}")
            else:
                print("  No author nodes found")
        except Exception as e:
            print(f"  Error checking author properties: {e}")
        
        # Check work properties
        print("\n5. Work Node Properties:")
        print("-" * 30)
        
        work_props_query = """
        MATCH (w:Work)
        RETURN keys(w) as properties
        LIMIT 1
        """
        
        try:
            result = client.run_cypher(work_props_query)
            if result:
                properties = result[0].get('properties', [])
                print(f"  Available properties: {', '.join(properties)}")
            else:
                print("  No work nodes found")
        except Exception as e:
            print(f"  Error checking work properties: {e}")
        
        # Check topic properties
        print("\n6. Topic Node Properties:")
        print("-" * 30)
        
        topic_props_query = """
        MATCH (t:Topic)
        RETURN keys(t) as properties
        LIMIT 1
        """
        
        try:
            result = client.run_cypher(topic_props_query)
            if result:
                properties = result[0].get('properties', [])
                print(f"  Available properties: {', '.join(properties)}")
            else:
                print("  No topic nodes found")
        except Exception as e:
            print(f"  Error checking topic properties: {e}")
        
        # Check for most collaborative authors
        print("\n7. Most Collaborative Authors:")
        print("-" * 30)
        
        collab_query = """
        MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(coauthor:Author)
        WHERE a <> coauthor
        WITH a, COUNT(DISTINCT coauthor) as collaborator_count
        WHERE collaborator_count > 0
        RETURN a.name as author_name, collaborator_count
        ORDER BY collaborator_count DESC
        LIMIT 10
        """
        
        try:
            result = client.run_cypher(collab_query)
            if result:
                print("  Top collaborative authors:")
                for i, record in enumerate(result, 1):
                    author = record.get('author_name', 'Unknown')
                    count = record.get('collaborator_count', 0)
                    print(f"    {i}. {author}: {count} collaborators")
            else:
                print("  No collaborative authors found")
        except Exception as e:
            print(f"  Error finding collaborative authors: {e}")
        
        # Recommendations
        print("\n8. Recommendations:")
        print("-" * 30)
        
        recommendations = []
        
        # Check if we have the basic data needed
        try:
            author_count = client.run_cypher("MATCH (n:Author) RETURN count(n) as count")[0]['count']
            work_count = client.run_cypher("MATCH (n:Work) RETURN count(n) as count")[0]['count']
            auth_rel_count = client.run_cypher("MATCH ()-[r:WORK_AUTHORED_BY]->() RETURN count(r) as count")[0]['count']
            
            if author_count == 0:
                recommendations.append("❌ No Author nodes found - need to load author data")
            elif author_count < 10:
                recommendations.append("⚠️  Very few authors - consider loading more author data")
            else:
                recommendations.append(f"✅ Good author coverage: {author_count:,} authors")
            
            if work_count == 0:
                recommendations.append("❌ No Work nodes found - need to load work data")
            elif work_count < 10:
                recommendations.append("⚠️  Very few works - consider loading more work data")
            else:
                recommendations.append(f"✅ Good work coverage: {work_count:,} works")
            
            if auth_rel_count == 0:
                recommendations.append("❌ No WORK_AUTHORED_BY relationships - this is critical for relationship inference!")
                recommendations.append("   Need to create relationships between authors and their works")
            else:
                recommendations.append(f"✅ Author-work relationships exist: {auth_rel_count:,} relationships")
            
            # Check co-authorship potential
            coauth_result = client.run_cypher("""
                MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
                WHERE a1 <> a2
                RETURN count(*) as count
            """)
            
            coauth_count = coauth_result[0]['count'] if coauth_result else 0
            
            if coauth_count == 0:
                recommendations.append("❌ No co-authorship patterns found")
                recommendations.append("   Either works have single authors or relationships are missing")
            else:
                recommendations.append(f"✅ Co-authorship patterns available: {coauth_count:,} instances")
        
        except Exception as e:
            recommendations.append(f"❌ Error analyzing database: {e}")
        
        for rec in recommendations:
            print(f"  {rec}")
        
        client.close()
        
        print("\n" + "=" * 50)
        print("Database structure analysis completed!")
        
    except Exception as e:
        logger.error(f"Database structure check failed: {e}")
        print(f"❌ Failed to analyze database structure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_database_structure()