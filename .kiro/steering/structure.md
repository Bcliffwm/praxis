# Project Structure

## Root Directory
- `.env`: Environment variables (AWS credentials, Neo4j connection details)
- `.python-version`: Python version specification (3.12.1)
- `README.md`: Project description and overview
- `.gitignore`: Git ignore patterns

## Core Notebooks
- `pyalex.ipynb`: Main data extraction notebook for OpenAlex API
- `neo4j_aura.ipynb`: Neo4j database ingestion and testing

## Data Directory (`data/`)
Contains CSV files generated from OpenAlex API:
- `works.csv`: Academic works/papers data
- `authors.csv`: Author information and metrics
- `topics.csv`: Research topics and classifications
- `institutions.csv`: Academic institutions
- `publishers.csv`: Publishing organizations
- `funders.csv`: Research funding organizations
- `work_auth_edges.csv`: Work-author relationships
- `work_topic_edges.csv`: Work-topic relationships
- `works_24_filtered.json`: Filtered works data in JSON format

## Virtual Environment (`praxis/`)
Python virtual environment containing:
- `Scripts/`: Executable scripts and activation files
- `Lib/site-packages/`: Installed Python packages
- `pyvenv.cfg`: Virtual environment configuration

## Configuration Directories
- `.kiro/`: Kiro IDE configuration and steering files
- `.vscode/`: VS Code workspace settings
- `.git/`: Git repository metadata

## Data Flow
1. **Extraction**: `pyalex.ipynb` → OpenAlex API → CSV files in `data/`
2. **Validation**: Pydantic models ensure data quality
3. **Storage**: `neo4j_aura.ipynb` → CSV data → Neo4j graph database
4. **Relationships**: Edge files create connections between entities

## Naming Conventions
- CSV files use snake_case naming
- OpenAlex IDs are cleaned (remove 'https://openalex.org/' prefix)
- Edge files represent relationships between entities
- JSON files contain filtered/processed data subsets