#!/usr/bin/env python3
"""
Create Co-authorship Relationships

This script creates additional WORK_AUTHORED_BY relationships to simulate
co-authorship patterns, enabling better testing of relationship inference.
"""

import sys
import random
import logging
from research_query_agent import ConfigManager, Neo4jClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_coauthorship_relationships(num_coauthorships=100):
    """Create co-authorship relationships by adding additional authors to existing works."""
    try:
        # Initialize configuration and client
        config_manager = ConfigManager()
        neo4j_config = config_manager.get_neo4j_config()
        
        client = Neo4jClient(
            uri=neo4j_config['uri'],
            auth=neo4j_config['auth'],
            database=neo4j_config['database']
        )
        
        print(f"Creating {num_coauthorships} co-authorship relationships...")
        print("=" * 50)
        
        # Get a sample of works that currently have only one author
        single_author_works_query = """
        MATCH (w:Work)<-[:WORK_AUTHORED_BY]-(a:Author)
        WITH w, COUNT(a) as author_count
        WHERE author_count = 1
        MATCH (w)<-[:WORK_AUTHORED_BY]-(existing_author:Author)
        RETURN w.id as work_id, w.title as work_title, existing_author.id as existing_author_id
        LIMIT $limit
        """
        
        works_result = client.run_cypher(single_author_works_query, {'limit': num_coauthorships})
        
        if not works_result:
            print("❌ No single-author works found to enhance with co-authors")
            return
        
        print(f"Found {len(works_result)} single-author works to enhance")
        
        # Get a pool of authors to use as co-authors
        authors_query = """
        MATCH (a:Author)
        RETURN a.id as author_id, a.name as author_name
        LIMIT 1000
        """
        
        authors_result = client.run_cypher(authors_query)
        author_pool = [(r['author_id'], r['author_name']) for r in authors_result]
        
        if len(author_pool) < 10:
            print("❌ Not enough authors in database to create meaningful co-authorships")
            return
        
        print(f"Using pool of {len(author_pool)} authors for co-authorship creation")
        
        # Create co-authorship relationships
        created_relationships = 0
        
        for i, work_record in enumerate(works_result):
            work_id = work_record['work_id']
            work_title = work_record['work_title']
            existing_author_id = work_record['existing_author_id']
            
            # Randomly select 1-3 additional co-authors
            num_coauthors = random.randint(1, 3)
            
            # Filter out the existing author from the pool
            available_authors = [a for a in author_pool if a[0] != existing_author_id]
            
            if len(available_authors) < num_coauthors:
                continue
            
            # Randomly select co-authors
            selected_coauthors = random.sample(available_authors, num_coauthors)
            
            # Create WORK_AUTHORED_BY relationships for each co-author
            for coauthor_id, coauthor_name in selected_coauthors:
                create_relationship_query = """
                MATCH (a:Author {id: $author_id}), (w:Work {id: $work_id})
                MERGE (a)-[:WORK_AUTHORED_BY]->(w)
                """
                
                try:
                    client.run_cypher(create_relationship_query, {
                        'author_id': coauthor_id,
                        'work_id': work_id
                    })
                    created_relationships += 1
                    
                    if created_relationships % 10 == 0:
                        print(f"  Created {created_relationships} relationships...")
                
                except Exception as e:
                    logger.warning(f"Failed to create relationship for author {coauthor_id} and work {work_id}: {e}")
            
            # Log progress
            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(works_result)} works")
        
        print(f"\n✅ Successfully created {created_relationships} co-authorship relationships")
        
        # Verify the results
        print("\nVerifying co-authorship creation...")
        
        coauth_check_query = """
        MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
        WHERE a1 <> a2
        RETURN count(*) as coauthorship_instances
        """
        
        result = client.run_cypher(coauth_check_query)
        coauth_count = result[0]['coauthorship_instances'] if result else 0
        
        print(f"Total co-authorship instances now: {coauth_count:,}")
        
        # Get sample co-authorships
        if coauth_count > 0:
            sample_query = """
            MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
            WHERE a1 <> a2
            RETURN a1.name as author1, a2.name as author2, w.title as work_title
            LIMIT 5
            """
            
            sample_result = client.run_cypher(sample_query)
            if sample_result:
                print("\nSample Co-authorships Created:")
                for i, record in enumerate(sample_result, 1):
                    print(f"  {i}. {record.get('author1', 'Unknown')} & {record.get('author2', 'Unknown')}")
                    print(f"     Work: {record.get('work_title', 'Unknown')[:60]}...")
        
        client.close()
        
        print("\n" + "=" * 50)
        print("Co-authorship relationship creation completed!")
        
    except Exception as e:
        logger.error(f"Failed to create co-authorship relationships: {e}")
        sys.exit(1)


def create_topic_based_collaborations(num_collaborations=50):
    """Create collaborations based on shared topics."""
    try:
        config_manager = ConfigManager()
        neo4j_config = config_manager.get_neo4j_config()
        
        client = Neo4jClient(
            uri=neo4j_config['uri'],
            auth=neo4j_config['auth'],
            database=neo4j_config['database']
        )
        
        print(f"\nCreating {num_collaborations} topic-based collaborations...")
        print("=" * 50)
        
        # Find authors who work on similar topics but haven't collaborated
        topic_similarity_query = """
        MATCH (a1:Author)-[:WORK_AUTHORED_BY]->(w1:Work)-[:WORK_HAS_TOPIC]->(t:Topic)<-[:WORK_HAS_TOPIC]-(w2:Work)<-[:WORK_AUTHORED_BY]-(a2:Author)
        WHERE a1 <> a2 
        AND NOT EXISTS((a1)-[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]-(a2))
        WITH a1, a2, t, COUNT(*) as shared_topic_count
        WHERE shared_topic_count >= 2
        RETURN a1.id as author1_id, a1.name as author1_name, 
               a2.id as author2_id, a2.name as author2_name,
               t.topic_name as shared_topic, shared_topic_count
        ORDER BY shared_topic_count DESC
        LIMIT $limit
        """
        
        potential_collabs = client.run_cypher(topic_similarity_query, {'limit': num_collaborations})
        
        if not potential_collabs:
            print("❌ No potential topic-based collaborations found")
            return
        
        print(f"Found {len(potential_collabs)} potential topic-based collaborations")
        
        # Create new collaborative works for these author pairs
        created_works = 0
        
        for i, collab in enumerate(potential_collabs):
            author1_id = collab['author1_id']
            author2_id = collab['author2_id']
            shared_topic = collab['shared_topic']
            
            # Create a new collaborative work
            work_id = f"W_COLLAB_{i+1:04d}"
            work_title = f"Collaborative Research on {shared_topic} - Study {i+1}"
            
            # Create the work node
            create_work_query = """
            CREATE (w:Work {
                id: $work_id,
                title: $work_title,
                type: 'collaborative-research',
                publication_date: date('2024-01-01')
            })
            """
            
            try:
                client.run_cypher(create_work_query, {
                    'work_id': work_id,
                    'work_title': work_title
                })
                
                # Create authorship relationships
                create_auth_query = """
                MATCH (a1:Author {id: $author1_id}), (a2:Author {id: $author2_id}), (w:Work {id: $work_id})
                CREATE (a1)-[:WORK_AUTHORED_BY]->(w)
                CREATE (a2)-[:WORK_AUTHORED_BY]->(w)
                """
                
                client.run_cypher(create_auth_query, {
                    'author1_id': author1_id,
                    'author2_id': author2_id,
                    'work_id': work_id
                })
                
                # Link to the shared topic
                link_topic_query = """
                MATCH (w:Work {id: $work_id}), (t:Topic {topic_name: $topic_name})
                CREATE (w)-[:WORK_HAS_TOPIC]->(t)
                """
                
                client.run_cypher(link_topic_query, {
                    'work_id': work_id,
                    'topic_name': shared_topic
                })
                
                created_works += 1
                
                if created_works % 10 == 0:
                    print(f"  Created {created_works} collaborative works...")
            
            except Exception as e:
                logger.warning(f"Failed to create collaborative work {work_id}: {e}")
        
        print(f"\n✅ Successfully created {created_works} topic-based collaborative works")
        
        client.close()
        
    except Exception as e:
        logger.error(f"Failed to create topic-based collaborations: {e}")


def main():
    """Main function to create co-authorship relationships."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create co-authorship relationships for testing")
    parser.add_argument('--coauthorships', type=int, default=100, 
                       help='Number of co-authorship relationships to create (default: 100)')
    parser.add_argument('--topic-collaborations', type=int, default=50,
                       help='Number of topic-based collaborations to create (default: 50)')
    parser.add_argument('--skip-coauth', action='store_true',
                       help='Skip creating basic co-authorship relationships')
    parser.add_argument('--skip-topics', action='store_true', 
                       help='Skip creating topic-based collaborations')
    
    args = parser.parse_args()
    
    print("Co-authorship Relationship Creator")
    print("=" * 40)
    
    try:
        if not args.skip_coauth:
            create_coauthorship_relationships(args.coauthorships)
        
        if not args.skip_topics:
            create_topic_based_collaborations(args.topic_collaborations)
        
        print("\n🎉 All relationship creation completed!")
        print("\nNext steps:")
        print("1. Run 'python check_database_structure.py' to verify the changes")
        print("2. Run 'python run_relationship_tests.py' to test the agent's capabilities")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()