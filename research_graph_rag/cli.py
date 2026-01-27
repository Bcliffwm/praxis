"""
Command-line interface for Research GraphRAG package.
"""

import argparse
import json
import sys
from typing import Dict, Any

from .core.config import ConfigManager
from .agents.base_agent import ResearchQueryAgent
from .agents.relationship_agent import EnhancedResearchQueryAgent
from .agents.network_agent import NetworkAnalysisAgent
from .agents.work_discovery_agent import WorkBasedDiscoveryAgent


def create_agent(agent_type: str, config_manager: ConfigManager):
    """Create an agent instance based on type."""
    agents = {
        "base": ResearchQueryAgent,
        "relationship": EnhancedResearchQueryAgent,
        "network": NetworkAnalysisAgent,
        "work_discovery": WorkBasedDiscoveryAgent
    }
    
    if agent_type not in agents:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(agents.keys())}")
    
    return agents[agent_type](config_manager)


def query_command(args):
    """Execute a query using the specified agent."""
    try:
        config_manager = ConfigManager(args.env_file)
        agent = create_agent(args.agent, config_manager)
        
        response = agent.query(args.query)
        
        if args.output_format == "json":
            print(json.dumps({"query": args.query, "response": response}, indent=2))
        else:
            print(f"Query: {args.query}")
            print(f"Response: {response}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def test_connection_command(args):
    """Test database connection."""
    try:
        config_manager = ConfigManager(args.env_file)
        agent = ResearchQueryAgent(config_manager)
        
        result = agent.test_connection()
        
        if args.output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Connection Status: {result['status']}")
            print(f"Message: {result['message']}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def database_info_command(args):
    """Get database information."""
    try:
        config_manager = ConfigManager(args.env_file)
        agent = ResearchQueryAgent(config_manager)
        
        info = agent.get_database_info()
        
        if args.output_format == "json":
            print(json.dumps(info, indent=2))
        else:
            print("Database Information:")
            print(f"  Database: {info.get('database', 'Unknown')}")
            print(f"  URI: {info.get('uri', 'Unknown')}")
            
            if 'nodes' in info:
                print("  Node Counts:")
                for node_info in info['nodes'][:5]:  # Show top 5
                    labels = ', '.join(node_info.get('labels', []))
                    count = node_info.get('count', 0)
                    print(f"    {labels}: {count}")
            
            if 'relationships' in info:
                print("  Relationship Counts:")
                for rel_info in info['relationships'][:5]:  # Show top 5
                    rel_type = rel_info.get('relationship_type', 'Unknown')
                    count = rel_info.get('count', 0)
                    print(f"    {rel_type}: {count}")
                    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def network_analysis_command(args):
    """Run network analysis."""
    try:
        config_manager = ConfigManager(args.env_file)
        agent = NetworkAnalysisAgent(config_manager)
        
        if args.method == "centrality":
            result = agent.get_centrality_metrics(limit=args.limit)
        elif args.method == "communities":
            result = agent.detect_communities()
        elif args.method == "related":
            if not args.title_keyword:
                print("Error: --title-keyword required for related works analysis", file=sys.stderr)
                sys.exit(1)
            result = agent.find_related_by_network_analysis(
                title_keyword=args.title_keyword,
                limit=args.limit
            )
        else:
            print(f"Error: Unknown network analysis method: {args.method}", file=sys.stderr)
            sys.exit(1)
        
        if args.output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Network Analysis Results ({args.method}):")
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Research GraphRAG - Graph-based research analysis toolkit"
    )
    
    parser.add_argument(
        "--env-file", 
        help="Path to .env file (default: .env in current directory)"
    )
    
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Execute a research query")
    query_parser.add_argument("query", help="Research query to execute")
    query_parser.add_argument(
        "--agent",
        choices=["base", "relationship", "network", "work_discovery"],
        default="base",
        help="Agent type to use (default: base)"
    )
    query_parser.set_defaults(func=query_command)
    
    # Test connection command
    test_parser = subparsers.add_parser("test", help="Test database connection")
    test_parser.set_defaults(func=test_connection_command)
    
    # Database info command
    info_parser = subparsers.add_parser("info", help="Get database information")
    info_parser.set_defaults(func=database_info_command)
    
    # Network analysis command
    network_parser = subparsers.add_parser("network", help="Run network analysis")
    network_parser.add_argument(
        "method",
        choices=["centrality", "communities", "related"],
        help="Network analysis method"
    )
    network_parser.add_argument(
        "--title-keyword",
        help="Title keyword for related works analysis"
    )
    network_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results (default: 20)"
    )
    network_parser.set_defaults(func=network_analysis_command)
    
    # Parse arguments and execute command
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()