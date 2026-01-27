# Research GraphRAG Package

A comprehensive Python package for research portfolio development using Graph-based Retrieval-Augmented Generation (GraphRAG) with Neo4j and AWS Bedrock.

## Features

- **Multiple Agent Types**: Specialized agents for different research analysis tasks
- **Neo4j Integration**: Robust graph database connectivity with error handling
- **AWS Bedrock Support**: AI-powered document summarization using Strands framework
- **Network Analysis**: Advanced graph algorithms using Neo4j Graph Data Science
- **Relationship Inference**: Discover latent connections between researchers and works
- **Work Discovery**: Find related works through multiple relationship patterns
- **Streamlit Interface**: Interactive web application for research analysis
- **CLI Tools**: Command-line interface for batch processing and automation

## Installation

### From Source
```bash
# Clone the repository
git clone <repository-url>
cd research-graph-rag

# Install in development mode
pip install -e .

# Or install with extras
pip install -e ".[dev,streamlit,jupyter]"
```

### Using Poetry
```bash
poetry install
poetry install --extras "dev streamlit jupyter"
```

## Quick Start

### 1. Configuration
Create a `.env` file in your project root:

```env
# Neo4j Configuration
DB_URI=bolt://localhost:7687
DB_USER=neo4j
DB_PASSWORD=your_password
TARGET_DB=praxis

# AWS Configuration
aws_access_key_id=YOUR_ACCESS_KEY
aws_secret_access_key=YOUR_SECRET_KEY
region_name=us-east-1
```

### 2. Basic Usage

```python
from research_graph_rag import ConfigManager, ResearchQueryAgent

# Initialize configuration
config_manager = ConfigManager()

# Create an agent
agent = ResearchQueryAgent(config_manager)

# Execute a query
response = agent.query("Find authors who have collaborated on machine learning research")
print(response)
```

### 3. Network Analysis

```python
from research_graph_rag import NetworkAnalysisAgent

# Create network analysis agent
network_agent = NetworkAnalysisAgent(config_manager)

# Find related works using network metrics
results = network_agent.find_related_by_network_analysis(
    title_keyword="machine learning",
    limit=10
)
```

### 4. Relationship Discovery

```python
from research_graph_rag import EnhancedResearchQueryAgent

# Create relationship agent
relationship_agent = EnhancedResearchQueryAgent(config_manager)

# Find co-authorship relationships
coauthors = relationship_agent.find_coauthorship_relationships(
    author_name="John Smith",
    limit=20
)
```

## Agent Types

### ResearchQueryAgent (Base)
- Basic Neo4j querying capabilities
- Cypher query validation and execution
- Database connection management

### EnhancedResearchQueryAgent
- Author relationship inference
- Co-authorship pattern detection
- Collaboration network analysis
- Shared research interest discovery

### NetworkAnalysisAgent
- Neo4j Graph Data Science integration
- Centrality measures (degree, betweenness, closeness, PageRank)
- Community detection using Louvain algorithm
- Shortest path analysis
- Node similarity calculations

### WorkBasedDiscoveryAgent
- Title-based work discovery
- Award number-based searches
- Author-based work finding
- Topic-based work clustering
- Comprehensive multi-method discovery

## Command Line Interface

```bash
# Test database connection
research-graph-rag test

# Get database information
research-graph-rag info

# Execute a query
research-graph-rag query "Find works about artificial intelligence" --agent network

# Run network analysis
research-graph-rag network centrality --limit 10
research-graph-rag network communities
research-graph-rag network related --title-keyword "machine learning"
```

## Streamlit Web Interface

Launch the interactive web application:

```bash
streamlit run streamlit_app.py
```

Features:
- Database overview and connection testing
- Interactive query interface
- Network analysis visualizations
- Centrality metrics charts
- Community detection results
- Related works discovery

## Configuration Management

The package uses a robust configuration system:

```python
from research_graph_rag import ConfigManager

# Load configuration
config_manager = ConfigManager()

# Get Neo4j configuration
neo4j_config = config_manager.get_neo4j_config()

# Get AWS configuration
aws_config = config_manager.get_aws_config()

# Get configuration summary (excludes sensitive data)
config_summary = config_manager.to_dict()
```

## Error Handling

The package provides comprehensive error handling:

```python
from research_graph_rag.utils.exceptions import (
    GraphRAGError, ConfigurationError, ValidationError
)

try:
    agent = ResearchQueryAgent(config_manager)
    response = agent.query("INVALID CYPHER QUERY")
except ValidationError as e:
    print(f"Query validation failed: {e}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except GraphRAGError as e:
    print(f"General error: {e}")
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=research_graph_rag

# Run specific test file
pytest tests/test_config.py
```

### Code Quality
```bash
# Format code
black research_graph_rag/

# Lint code
flake8 research_graph_rag/

# Type checking
mypy research_graph_rag/
```

## Architecture

```
research_graph_rag/
├── core/                   # Core functionality
│   ├── config.py          # Configuration management
│   ├── database.py        # Neo4j client
│   └── models.py          # Data models
├── agents/                 # Specialized agents
│   ├── base_agent.py      # Base agent class
│   ├── relationship_agent.py  # Relationship inference
│   ├── network_agent.py   # Network analysis
│   └── work_discovery_agent.py  # Work discovery
├── utils/                  # Utilities
│   ├── validators.py      # Query validation
│   ├── exceptions.py      # Custom exceptions
│   └── gds_queries.py     # GDS query templates
└── cli.py                 # Command-line interface
```

## Requirements

- Python 3.12+
- Neo4j 4.4+ (with Graph Data Science library for network analysis)
- AWS account with Bedrock access
- Required Python packages (see requirements.txt)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Support

For issues and questions:
- Check the documentation
- Review existing issues
- Create a new issue with detailed information