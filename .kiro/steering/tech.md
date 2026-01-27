# Technology Stack

## Build System & Package Management
- **Poetry**: Primary dependency management and build system
- **Python 3.12.1**: Required Python version
- **Virtual Environment**: Located in `praxis/` folder

## Core Technologies
- **PyAlex**: Academic research data extraction from OpenAlex API
- **Neo4j**: Graph database for storing research entity relationships
- **AWS Bedrock**: AI model hosting for document summarization
- **Strands Agents**: AI agent framework for research analysis tasks
- **Jupyter**: Interactive development and data analysis environment

## Key Libraries
- `neo4j`: Graph database driver
- `boto3`: AWS SDK for Bedrock integration
- `strands-agents`: AI agent framework
- `pydantic`: Data validation and modeling
- `python-dotenv`: Environment configuration management
- `beautifulsoup4`: Web scraping and HTML parsing
- `httpx`: HTTP client for API requests

## Common Commands

### Environment Setup
```bash
# Activate virtual environment
praxis\Scripts\activate

# Install dependencies
poetry install

# Update dependencies
poetry update
```

### Development
```bash
# Start Jupyter notebook server
jupyter notebook

# Run Python scripts
python script_name.py

# Install new package
poetry add package_name
```

### Database
- Neo4j should be running locally on `bolt://127.0.0.1:7687`
- Default database: `praxis`
- Credentials configured in `.env` file

## Configuration
- Environment variables in `.env` file (AWS credentials, Neo4j connection)
- PyAlex API requires email configuration: `pyalex.config.email`
- AWS region: `us-east-1`