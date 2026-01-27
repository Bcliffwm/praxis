#!/usr/bin/env python3
"""
Run Author Relationship Inference Tests

This script runs comprehensive tests to evaluate the agent's ability to infer
relationships between authors and discover latent research connections.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Import test modules
from test_author_relationship_inference import AuthorRelationshipTester
from enhanced_relationship_agent import EnhancedResearchQueryAgent, ConfigManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_basic_tests():
    """Run basic relationship inference tests with the standard agent."""
    logger.info("Running basic relationship inference tests...")
    
    try:
        tester = AuthorRelationshipTester()
        report = tester.run_all_tests()
        return report
    except Exception as e:
        logger.error(f"Basic tests failed: {e}")
        return None


def run_enhanced_tests():
    """Run enhanced relationship inference tests with the enhanced agent."""
    logger.info("Running enhanced relationship inference tests...")
    
    try:
        # Initialize enhanced agent
        config_manager = ConfigManager()
        enhanced_agent = EnhancedResearchQueryAgent(config_manager)
        
        # Test specific relationship inference capabilities
        test_queries = [
            # Co-authorship detection
            "Find pairs of authors who have co-authored works together",
            
            # Collaboration networks
            "Show me the top 10 most collaborative authors based on number of co-authors",
            
            # Shared research interests
            "Find authors who work on similar topics through their publications",
            
            # Indirect collaborations
            "Identify authors who haven't collaborated directly but share common co-authors",
            
            # Research domain clustering
            "Group authors by their research domains based on collaboration patterns",
            
            # Cross-institutional collaboration
            "Find collaboration patterns between authors from different institutions"
        ]
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"Enhanced Test {i}: {query}")
            
            try:
                response = enhanced_agent.query(query)
                
                result = {
                    'test_number': i,
                    'query': query,
                    'response': str(response),
                    'success': _evaluate_enhanced_response(response),
                    'timestamp': datetime.now().isoformat()
                }
                
                results.append(result)
                logger.info(f"  Result: {'PASS' if result['success'] else 'FAIL'}")
                
            except Exception as e:
                logger.error(f"  Error: {e}")
                results.append({
                    'test_number': i,
                    'query': query,
                    'error': str(e),
                    'success': False,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Calculate success rate
        successful = sum(1 for r in results if r.get('success', False))
        success_rate = (successful / len(results) * 100) if results else 0
        
        enhanced_report = {
            'test_type': 'enhanced_relationship_inference',
            'total_tests': len(results),
            'successful_tests': successful,
            'success_rate': f"{success_rate:.1f}%",
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        return enhanced_report
        
    except Exception as e:
        logger.error(f"Enhanced tests failed: {e}")
        return None


def _evaluate_enhanced_response(response) -> bool:
    """Evaluate enhanced response for relationship inference success."""
    response_str = str(response).lower()
    
    # Check for successful relationship detection indicators
    success_indicators = [
        'records',
        'row_count',
        'enhanced_analysis',
        'relationships',
        'collaboration',
        'co-author',
        'topic',
        'author',
        'work'
    ]
    
    # Check for error indicators
    error_indicators = [
        'error',
        'failed',
        'validation_error',
        'connection_error',
        'execution_error'
    ]
    
    has_success = any(indicator in response_str for indicator in success_indicators)
    has_error = any(indicator in response_str for indicator in error_indicators)
    
    return has_success and not has_error


def compare_agents():
    """Compare basic vs enhanced agent performance."""
    logger.info("Comparing basic vs enhanced agent performance...")
    
    # Test queries for comparison
    comparison_queries = [
        "Find authors who have worked together on publications",
        "Show me collaboration networks in the research data",
        "Which authors share similar research interests?",
        "Identify potential research partnerships"
    ]
    
    try:
        # Initialize both agents
        config_manager = ConfigManager()
        from research_query_agent import ResearchQueryAgent
        basic_agent = ResearchQueryAgent(config_manager)
        enhanced_agent = EnhancedResearchQueryAgent(config_manager)
        
        comparison_results = []
        
        for i, query in enumerate(comparison_queries, 1):
            logger.info(f"Comparison Test {i}: {query}")
            
            # Test basic agent
            try:
                basic_response = basic_agent.query(query)
                basic_success = _evaluate_enhanced_response(basic_response)
            except Exception as e:
                basic_response = f"Error: {e}"
                basic_success = False
            
            # Test enhanced agent
            try:
                enhanced_response = enhanced_agent.query(query)
                enhanced_success = _evaluate_enhanced_response(enhanced_response)
            except Exception as e:
                enhanced_response = f"Error: {e}"
                enhanced_success = False
            
            comparison_results.append({
                'query': query,
                'basic_agent': {
                    'response': str(basic_response),
                    'success': basic_success
                },
                'enhanced_agent': {
                    'response': str(enhanced_response),
                    'success': enhanced_success
                },
                'improvement': enhanced_success and not basic_success
            })
            
            logger.info(f"  Basic: {'PASS' if basic_success else 'FAIL'}")
            logger.info(f"  Enhanced: {'PASS' if enhanced_success else 'FAIL'}")
            logger.info(f"  Improvement: {'YES' if enhanced_success and not basic_success else 'NO'}")
        
        return comparison_results
        
    except Exception as e:
        logger.error(f"Agent comparison failed: {e}")
        return None


def generate_comprehensive_report(basic_report, enhanced_report, comparison_results):
    """Generate a comprehensive test report."""
    logger.info("Generating comprehensive test report...")
    
    report = {
        'test_summary': {
            'timestamp': datetime.now().isoformat(),
            'test_types': ['basic_relationship_inference', 'enhanced_relationship_inference', 'agent_comparison']
        },
        'basic_agent_results': basic_report,
        'enhanced_agent_results': enhanced_report,
        'agent_comparison': comparison_results,
        'recommendations': []
    }
    
    # Generate recommendations based on results
    if basic_report and enhanced_report:
        basic_success_rate = float(basic_report['summary']['success_rate'].rstrip('%'))
        enhanced_success_rate = float(enhanced_report['success_rate'].rstrip('%'))
        
        if enhanced_success_rate > basic_success_rate:
            report['recommendations'].append(
                "Enhanced agent shows improved relationship inference capabilities. "
                "Consider adopting the enhanced agent for production use."
            )
        
        if basic_success_rate < 50:
            report['recommendations'].append(
                "Basic agent shows poor relationship inference performance. "
                "Review VALID_RELATIONSHIPS configuration and add explicit co-authorship relationships."
            )
        
        if enhanced_success_rate < 70:
            report['recommendations'].append(
                "Enhanced agent needs improvement. Consider adding more relationship types "
                "and improving Cypher query patterns for complex relationships."
            )
    
    # Add general recommendations
    report['recommendations'].extend([
        "Ensure author-work relationships exist in the Neo4j database",
        "Consider adding explicit COLLABORATED_WITH relationships for better performance",
        "Test with larger datasets to validate relationship inference at scale",
        "Implement caching for frequently used relationship queries"
    ])
    
    # Save comprehensive report
    import json
    report_file = f"comprehensive_relationship_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Comprehensive report saved to: {report_file}")
    
    return report, report_file


def main():
    """Main function to run relationship inference tests."""
    parser = argparse.ArgumentParser(
        description="Run Author Relationship Inference Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--test-type',
        choices=['basic', 'enhanced', 'comparison', 'all'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("Author Relationship Inference Test Suite")
    print("=" * 50)
    print(f"Test Type: {args.test_type}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    basic_report = None
    enhanced_report = None
    comparison_results = None
    
    try:
        if args.test_type in ['basic', 'all']:
            print("\n🔍 Running Basic Relationship Inference Tests...")
            basic_report = run_basic_tests()
        
        if args.test_type in ['enhanced', 'all']:
            print("\n🚀 Running Enhanced Relationship Inference Tests...")
            enhanced_report = run_enhanced_tests()
        
        if args.test_type in ['comparison', 'all']:
            print("\n⚖️  Running Agent Comparison Tests...")
            comparison_results = compare_agents()
        
        # Generate comprehensive report
        if args.test_type == 'all':
            print("\n📊 Generating Comprehensive Report...")
            report, report_file = generate_comprehensive_report(
                basic_report, enhanced_report, comparison_results
            )
            
            print(f"\n✅ All tests completed!")
            print(f"📄 Comprehensive report: {report_file}")
        
        print("\n" + "=" * 50)
        print("TEST EXECUTION COMPLETED")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()