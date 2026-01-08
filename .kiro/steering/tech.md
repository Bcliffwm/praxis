# Technology Stack

## Core Technologies
- **Python 3.12.1**: Primary programming language
- **Jupyter Notebooks**: Interactive development and data analysis
- **Neo4j**: Graph database for storing research relationships
- **PyAlex**: Python client for OpenAlex API data extraction
- **Pydantic**: Data validation and serialization

## Key Libraries
- `pyalex`: OpenAlex API client for academic data
- `neo4j`: Neo4j database driver
- `pydantic`: Data validation models
- `csv`: CSV file processing
- `json`: JSON data handling
- `itertools`: Data processing utilities

## Environment Setup
- Virtual environment: `praxis/` directory
- Python version managed via `.python-version` file
- Environment variables stored in `.env` file (AWS credentials, Neo4j connection)

## Database Configuration
- **Neo4j Connection**: Local instance at `bolt://127.0.0.1:7687`
- **Target Database**: `praxis` (configurable via `TARGET_DB`)
- **Authentication**: Username/password stored in environment variables

## Common Commands
```bash
# Activate virtual environment (Windows)
praxis\Scripts\activate

# Start Jupyter notebook
jupyter notebook

# Connect to Neo4j (ensure Neo4j is running locally)
# Default: bolt://127.0.0.1:7687
```

## Data Processing Pipeline
1. Extract data from OpenAlex API using PyAlex
2. Validate data using Pydantic models
3. Export to CSV files in `data/` directory
4. Ingest CSV data into Neo4j graph database
5. Create relationships between entities (works, authors, topics)