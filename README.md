# Research GraphRAG - Praxis Project

This is a Praxis project focused on "Enhancing Document Summarization for Research Portfolio Development with GraphRAG".

## 🚀 Package Organization Complete

The project has been successfully organized into a production-ready Python package with the following structure:

### 📦 Package Structure
```
research_graph_rag/
├── core/                   # Core functionality
│   ├── config.py          # Configuration management
│   ├── database.py        # Neo4j client with error handling
│   └── models.py          # Pydantic data models
├── agents/                 # Specialized AI agents
│   ├── base_agent.py      # Base research query agent
│   ├── relationship_agent.py  # Author relationship inference
│   ├── network_agent.py   # Network analysis with GDS
│   └── work_discovery_agent.py  # Work-based discovery
├── utils/                  # Utilities and validation
│   ├── validators.py      # Cypher query validation
│   ├── exceptions.py      # Custom exception classes
│   └── gds_queries.py     # Neo4j GDS query templates
└── cli.py                 # Command-line interface
```

### 🛠️ Installation & Usage

#### Quick Install
```bash
# Install the package
pip install -e .

# With development extras
pip install -e ".[dev,streamlit,jupyter]"
```

#### Command Line Interface
```bash
# Test database connection
research-graph-rag test

# Execute queries
research-graph-rag query "Find collaborative authors" --agent relationship

# Network analysis
research-graph-rag network centrality --limit 10
```

#### Streamlit Web Interface
```bash
streamlit run streamlit_app.py
```

#### Python API
```python
from research_graph_rag import (
    ConfigManager, ResearchQueryAgent, 
    NetworkAnalysisAgent, EnhancedResearchQueryAgent
)

# Initialize and use agents
config = ConfigManager()
agent = NetworkAnalysisAgent(config)
results = agent.find_related_by_network_analysis(title_keyword="AI")
```

### 🎯 Key Features Implemented

1. **Modular Architecture**: Clean separation of concerns with specialized agents
2. **Robust Configuration**: Environment-based config with validation
3. **Error Handling**: Comprehensive exception handling and user-friendly messages
4. **Multiple Interfaces**: CLI, Python API, and Streamlit web interface
5. **Production Ready**: Docker support, health checks, and deployment guides
6. **Testing Framework**: Unit tests with pytest
7. **Documentation**: Comprehensive README and deployment guides

### 📊 Agent Capabilities

- **Base Agent**: Core Neo4j querying with Cypher validation
- **Relationship Agent**: Co-authorship and collaboration analysis
- **Network Agent**: Advanced graph algorithms (centrality, communities)
- **Work Discovery Agent**: Multi-method work finding and relationship discovery

### 🔧 Development Tools

- **CLI Interface**: `research_graph_rag/cli.py`
- **Streamlit App**: `streamlit_app.py`
- **Docker Support**: Multi-stage Dockerfile and docker-compose
- **Testing**: `tests/` directory with pytest configuration
- **Package Setup**: `setup.py` for pip installation

### 📚 Documentation

- **Package README**: `research_graph_rag/README.md` - Detailed package documentation
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md` - Production deployment instructions
- **Original Notebooks**: Core analysis notebooks remain for development and exploration

### 🏗️ Original Project Structure Preserved

The original project structure with notebooks and demo files has been preserved:
- `pyalex.ipynb`, `neo4j_aura.ipynb`, `bedrock_strands.ipynb` - Core notebooks
- `demo_*.py` files - Demonstration scripts
- `data/` directory - Research data files
- All existing functionality remains accessible

### 🚀 Next Steps

The package is now ready for:
1. **Streamlit Deployment**: Interactive web interface for research analysis
2. **Production Use**: Robust error handling and configuration management
3. **Development**: Modular architecture supports easy extension
4. **Distribution**: Can be packaged and distributed via PyPI

See `DEPLOYMENT_GUIDE.md` for detailed deployment instructions and `research_graph_rag/README.md` for package-specific documentation.
