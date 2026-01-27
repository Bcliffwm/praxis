# Project Structure

## Root Directory
- `README.md`: Project description and overview
- `pyproject.toml`: Poetry configuration and dependencies
- `requirements.txt`: Pip-compatible dependency list
- `.python-version`: Python version specification (3.12.1)
- `.env`: Environment variables (AWS credentials, Neo4j config)
- `.gitignore`: Git ignore patterns

## Core Notebooks
- `pyalex.ipynb`: Data extraction from OpenAlex API using PyAlex
- `neo4j_aura.ipynb`: Neo4j database operations and graph queries
- `bedrock_strands.ipynb`: AWS Bedrock integration with Strands agents

## Data Directory (`data/`)
Contains CSV files and processed data:
- `works.csv`: Academic works/papers data
- `authors.csv`: Author information
- `institutions.csv`: Academic institutions
- `publishers.csv`: Publishing organizations
- `topics.csv`: Research topics/subjects
- `funders.csv`: Funding organizations
- `work_auth_edges.csv`: Work-author relationships
- `work_topic_edges.csv`: Work-topic relationships
- `works_24_filtered.json`: Processed works data in JSON format

## Virtual Environment (`praxis/`)
Poetry-managed virtual environment containing:
- `Scripts/`: Executable binaries and activation scripts
- `Lib/site-packages/`: Installed Python packages
- `Include/`: Header files
- `share/`: Shared resources (Jupyter kernels, man pages)

## Configuration Directories
- `.kiro/`: Kiro IDE configuration and steering files
- `.vscode/`: VS Code workspace settings
- `.git/`: Git repository metadata

## Data Flow Pattern
1. **Extract**: PyAlex notebook pulls academic data from OpenAlex API
2. **Transform**: Data processed into CSV format in `data/` directory
3. **Load**: Neo4j notebook loads CSV data into graph database
4. **Analyze**: Strands agents query graph data for summarization tasks

## File Naming Conventions
- Notebooks: Descriptive names indicating primary technology (`pyalex.ipynb`, `neo4j_aura.ipynb`)
- Data files: Entity type + format (`works.csv`, `authors.csv`)
- Edge files: Relationship pattern (`work_auth_edges.csv`, `work_topic_edges.csv`)
