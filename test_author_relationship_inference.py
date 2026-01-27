#!/usr/bin/env python3
"""
Test Author Relationship Inference

This script tests the research query agent's ability to infer relationships between authors
based on co-authorship patterns and discover latent topics, works, and related research efforts.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import the research query agent
from research_query_agent import ConfigManager, ResearchQueryAgent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AuthorRelationshipTester:
    """Test suite for author relationship inference capabilities."""
    
    def __init__(self):
        """Initialize the tester with the research query agent."""
        self.config_manager = ConfigManager()
        self.agent = ResearchQueryAgent(self.config_manager)
        self.test_results = []
    
    def run_all_tests(self):
        """Run all relationship inference tests."""
        logger.info("Starting Author Relationship Inference Tests")
        
        # Test 1: Basic co-authorship detection
        self.test_coauthorship_detection()
        
        # Test 2: Author collaboration networks
        self.test_collaboration_networks()
        
        # Test 3: Shared topic inference
        self.test_shared_topic_inference()
        
        # Test 4: Research domain clustering
        self.test_research_domain_clustering()
        
        # Test 5: Latent relationship discovery
        self.test_latent_relationship_discovery()
        
        # Test 6: Cross-institutional collaboration
        self.test_cross_institutional_collaboration()
        
        # Generate summary report
        self.generate_test_report()
    
    def test_coauthorship_detection(self):
        """Test 1: Basic Co-authorship Detection
        
        Tests if the agent can identify authors who have co-authored works together.
        """
        logger.info("Test 1: Basic Co-authorship Detection")
        
        test_queries = [
            "Find pairs of authors who have co-authored works together",
            "Show me authors who have collaborated on the same publications",
            "Which authors have worked together on research papers?",
            "Identify co-authorship relationships in the database"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"  Query {i}: {query}")
            try:
                response = self.agent.query(query)
                result = {
                    'test': 'coauthorship_detection',
                    'query_number': i,
                    'query': query,
                    'response': str(response),
                    'success': self._evaluate_coauthorship_response(response)
                }
                self.test_results.append(result)
                logger.info(f"    Result: {'PASS' if result['success'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"    Error: {e}")
                self.test_results.append({
                    'test': 'coauthorship_detection',
                    'query_number': i,
                    'query': query,
                    'error': str(e),
                    'success': False
                })
    
    def test_collaboration_networks(self):
        """Test 2: Author Collaboration Networks
        
        Tests if the agent can identify broader collaboration networks and patterns.
        """
        logger.info("Test 2: Author Collaboration Networks")
        
        test_queries = [
            "Find the most collaborative authors based on number of co-authors",
            "Show me authors who form collaboration clusters or networks",
            "Which authors have the most diverse collaboration patterns?",
            "Identify research collaboration hubs in the author network"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"  Query {i}: {query}")
            try:
                response = self.agent.query(query)
                result = {
                    'test': 'collaboration_networks',
                    'query_number': i,
                    'query': query,
                    'response': str(response),
                    'success': self._evaluate_network_response(response)
                }
                self.test_results.append(result)
                logger.info(f"    Result: {'PASS' if result['success'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"    Error: {e}")
                self.test_results.append({
                    'test': 'collaboration_networks',
                    'query_number': i,
                    'query': query,
                    'error': str(e),
                    'success': False
                })
    
    def test_shared_topic_inference(self):
        """Test 3: Shared Topic Inference
        
        Tests if the agent can infer shared research interests based on co-authorship.
        """
        logger.info("Test 3: Shared Topic Inference")
        
        test_queries = [
            "Find authors who work on similar topics based on their co-authored works",
            "Show me research topics that connect different authors",
            "Which authors share common research interests through their collaborations?",
            "Identify topic clusters formed by author collaborations"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"  Query {i}: {query}")
            try:
                response = self.agent.query(query)
                result = {
                    'test': 'shared_topic_inference',
                    'query_number': i,
                    'query': query,
                    'response': str(response),
                    'success': self._evaluate_topic_response(response)
                }
                self.test_results.append(result)
                logger.info(f"    Result: {'PASS' if result['success'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"    Error: {e}")
                self.test_results.append({
                    'test': 'shared_topic_inference',
                    'query_number': i,
                    'query': query,
                    'error': str(e),
                    'success': False
                })
    
    def test_research_domain_clustering(self):
        """Test 4: Research Domain Clustering
        
        Tests if the agent can identify research domains based on author relationships.
        """
        logger.info("Test 4: Research Domain Clustering")
        
        test_queries = [
            "Group authors into research domains based on their collaboration patterns",
            "Find research communities formed by author collaborations",
            "Show me how authors cluster around specific research areas",
            "Identify interdisciplinary research connections between author groups"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"  Query {i}: {query}")
            try:
                response = self.agent.query(query)
                result = {
                    'test': 'research_domain_clustering',
                    'query_number': i,
                    'query': query,
                    'response': str(response),
                    'success': self._evaluate_clustering_response(response)
                }
                self.test_results.append(result)
                logger.info(f"    Result: {'PASS' if result['success'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"    Error: {e}")
                self.test_results.append({
                    'test': 'research_domain_clustering',
                    'query_number': i,
                    'query': query,
                    'error': str(e),
                    'success': False
                })
    
    def test_latent_relationship_discovery(self):
        """Test 5: Latent Relationship Discovery
        
        Tests if the agent can discover indirect relationships and potential collaborations.
        """
        logger.info("Test 5: Latent Relationship Discovery")
        
        test_queries = [
            "Find authors who haven't collaborated directly but share common co-authors",
            "Identify potential research collaborations based on shared interests",
            "Show me authors who work on related topics but haven't co-authored together",
            "Discover hidden connections between authors through their collaboration networks"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"  Query {i}: {query}")
            try:
                response = self.agent.query(query)
                result = {
                    'test': 'latent_relationship_discovery',
                    'query_number': i,
                    'query': query,
                    'response': str(response),
                    'success': self._evaluate_latent_response(response)
                }
                self.test_results.append(result)
                logger.info(f"    Result: {'PASS' if result['success'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"    Error: {e}")
                self.test_results.append({
                    'test': 'latent_relationship_discovery',
                    'query_number': i,
                    'query': query,
                    'error': str(e),
                    'success': False
                })
    
    def test_cross_institutional_collaboration(self):
        """Test 6: Cross-institutional Collaboration
        
        Tests if the agent can identify collaboration patterns across institutions.
        """
        logger.info("Test 6: Cross-institutional Collaboration")
        
        test_queries = [
            "Find authors from different institutions who collaborate together",
            "Show me cross-institutional research partnerships",
            "Which institutions have the strongest collaboration networks?",
            "Identify inter-institutional research connections"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"  Query {i}: {query}")
            try:
                response = self.agent.query(query)
                result = {
                    'test': 'cross_institutional_collaboration',
                    'query_number': i,
                    'query': query,
                    'response': str(response),
                    'success': self._evaluate_institutional_response(response)
                }
                self.test_results.append(result)
                logger.info(f"    Result: {'PASS' if result['success'] else 'FAIL'}")
            except Exception as e:
                logger.error(f"    Error: {e}")
                self.test_results.append({
                    'test': 'cross_institutional_collaboration',
                    'query_number': i,
                    'query': query,
                    'error': str(e),
                    'success': False
                })
    
    def _evaluate_coauthorship_response(self, response: str) -> bool:
        """Evaluate if the response successfully identifies co-authorship relationships."""
        response_str = str(response).lower()
        
        # Check for indicators of successful co-authorship detection
        success_indicators = [
            'co-author',
            'collaborated',
            'worked together',
            'shared work',
            'joint publication',
            'partnership',
            'author pairs',
            'collaboration'
        ]
        
        # Check for data indicators
        data_indicators = [
            'records',
            'row_count',
            'results',
            'found',
            'match'
        ]
        
        has_success_indicator = any(indicator in response_str for indicator in success_indicators)
        has_data_indicator = any(indicator in response_str for indicator in data_indicators)
        
        # Check for error indicators
        error_indicators = [
            'error',
            'failed',
            'no results',
            'empty',
            'not found'
        ]
        
        has_error = any(indicator in response_str for indicator in error_indicators)
        
        return has_success_indicator and has_data_indicator and not has_error
    
    def _evaluate_network_response(self, response: str) -> bool:
        """Evaluate if the response successfully identifies collaboration networks."""
        response_str = str(response).lower()
        
        success_indicators = [
            'network',
            'cluster',
            'hub',
            'collaborative',
            'most',
            'diverse',
            'pattern',
            'connection'
        ]
        
        return any(indicator in response_str for indicator in success_indicators)
    
    def _evaluate_topic_response(self, response: str) -> bool:
        """Evaluate if the response successfully identifies shared topics."""
        response_str = str(response).lower()
        
        success_indicators = [
            'topic',
            'research interest',
            'similar',
            'common',
            'shared',
            'subject',
            'field'
        ]
        
        return any(indicator in response_str for indicator in success_indicators)
    
    def _evaluate_clustering_response(self, response: str) -> bool:
        """Evaluate if the response successfully identifies research domain clusters."""
        response_str = str(response).lower()
        
        success_indicators = [
            'cluster',
            'group',
            'domain',
            'community',
            'area',
            'interdisciplinary',
            'research'
        ]
        
        return any(indicator in response_str for indicator in success_indicators)
    
    def _evaluate_latent_response(self, response: str) -> bool:
        """Evaluate if the response successfully identifies latent relationships."""
        response_str = str(response).lower()
        
        success_indicators = [
            'potential',
            'indirect',
            'hidden',
            'latent',
            'common',
            'shared',
            'related',
            'connection'
        ]
        
        return any(indicator in response_str for indicator in success_indicators)
    
    def _evaluate_institutional_response(self, response: str) -> bool:
        """Evaluate if the response successfully identifies institutional collaborations."""
        response_str = str(response).lower()
        
        success_indicators = [
            'institution',
            'cross-institutional',
            'inter-institutional',
            'partnership',
            'different',
            'collaboration'
        ]
        
        return any(indicator in response_str for indicator in success_indicators)
    
    def generate_test_report(self):
        """Generate a comprehensive test report."""
        logger.info("Generating Test Report")
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.get('success', False))
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group results by test type
        test_groups = {}
        for result in self.test_results:
            test_type = result.get('test', 'unknown')
            if test_type not in test_groups:
                test_groups[test_type] = []
            test_groups[test_type].append(result)
        
        # Generate report
        report = {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': f"{success_rate:.1f}%"
            },
            'test_groups': {},
            'detailed_results': self.test_results
        }
        
        # Add group statistics
        for test_type, results in test_groups.items():
            group_total = len(results)
            group_success = sum(1 for r in results if r.get('success', False))
            group_rate = (group_success / group_total * 100) if group_total > 0 else 0
            
            report['test_groups'][test_type] = {
                'total': group_total,
                'successful': group_success,
                'success_rate': f"{group_rate:.1f}%"
            }
        
        # Save report to file
        report_file = 'author_relationship_test_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("AUTHOR RELATIONSHIP INFERENCE TEST REPORT")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print("\nTest Group Results:")
        
        for test_type, stats in report['test_groups'].items():
            print(f"  {test_type.replace('_', ' ').title()}: {stats['successful']}/{stats['total']} ({stats['success_rate']})")
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return report


def main():
    """Main function to run the author relationship inference tests."""
    try:
        # Initialize and run tests
        tester = AuthorRelationshipTester()
        report = tester.run_all_tests()
        
        # Print recommendations based on results
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        success_rate = float(report['summary']['success_rate'].rstrip('%'))
        
        if success_rate >= 80:
            print("✅ Excellent! The agent demonstrates strong relationship inference capabilities.")
            print("   Consider expanding to more complex relationship patterns.")
        elif success_rate >= 60:
            print("⚠️  Good performance with room for improvement.")
            print("   Focus on enhancing query understanding and relationship detection.")
        elif success_rate >= 40:
            print("⚠️  Moderate performance. Several areas need improvement:")
            print("   - Review relationship definitions in VALID_RELATIONSHIPS")
            print("   - Enhance Cypher query generation for complex relationships")
            print("   - Consider adding more relationship types to the schema")
        else:
            print("❌ Poor performance. Major improvements needed:")
            print("   - Check if author-work relationships exist in the database")
            print("   - Verify VALID_RELATIONSHIPS configuration")
            print("   - Review agent's understanding of relationship queries")
            print("   - Consider adding explicit co-authorship relationships to schema")
        
        print("\nNext Steps:")
        print("1. Review failed test queries to understand limitations")
        print("2. Enhance the agent's relationship inference capabilities")
        print("3. Consider adding new relationship types to VALID_RELATIONSHIPS")
        print("4. Test with more complex multi-hop relationship queries")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()