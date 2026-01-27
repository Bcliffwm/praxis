# Design Document

## Overview

This design converts the bedrock_strands.ipynb notebook into a standalone Python script called `research_query_agent.py`. The script will maintain all existing functionality while adding a proper CLI interface, structured error handling, and both single-query and interactive modes.

## Architecture

The script follows a modular architecture with clear separation of concerns:

```
research_query_agent.py
├── Configuration Management
├── Neo4j Database Layer  
├── Cypher Validation Layer
├── Strands Agent Layer
├── CLI Interface Layer
└── Main Execution Logic
```

## Components and Interfaces

### 1. Configuration Manager
```python
class ConfigManager:
    def __init__(self):
        self.load_environment()
        self.validate_config()
    
    def load_environment(self) -> None
    def validate_config(self) -> None
    def get_neo4j_config(self) -> dict
    def get_aws_config(self) -> dict
```

**Purpose**: Centralized configuration loading and validation
**Dependencies**: python-dotenv, os

### 2. Neo4j Database Client
```python
class Neo4jClient:
    def __init__(self, uri: str, auth: tuple, database: str)
    def close(self) -> None
    def run_cypher(self, query: str, params: Dict[str, Any] | None = None) -> List[Dict]
```

**Purpose**: Database connectivity and query execution
**Dependencies**: neo4j driver

### 3. Cypher Validation System
```python
class CypherValidator:
    @staticmethod
    def assert_read_only(cypher: str) -> None
    @staticmethod
    def validate_properties(cypher: str) -> None
    @staticmethod
    def normalize_properties(cypher: str) -> str
    @staticmethod
    def normalize_relationships(cypher: str) -> str
    @staticmethod
    def validate_labels(cypher: str) -> None
    @staticmethod
    def prepare_cypher(cypher: str) -> str
```

**Purpose**: Ensure query safety and normalize syntax
**Dependencies**: re, typing

### 4. Research Query Agent
```python
class ResearchQueryAgent:
    def __init__(self, config_manager: ConfigManager)
    def initialize_bedrock_model(self) -> BedrockModel
    def create_neo4j_tool(self) -> callable
    def setup_agent(self) -> Agent
    def query(self, question: str) -> str
    def close(self) -> None
```

**Purpose**: Strands agent setup and query processing
**Dependencies**: strands, boto3, pydantic

### 5. CLI Interface
```python
class CLIInterface:
    def __init__(self, agent: ResearchQueryAgent)
    def parse_arguments(self) -> argparse.Namespace
    def run_single_query(self, query: str) -> None
    def run_interactive_mode(self) -> None
    def format_results(self, response: str) -> str
    def handle_error(self, error: Exception) -> None
```

**Purpose**: Command-line interface and user interaction
**Dependencies**: argparse, sys

## Data Models

### Pydantic Models (Preserved from notebook)
```python
class MatchPattern(BaseModel):
    start_label: AuthorLabel
    relationship: RelationshipType  
    end_label: WorkLabel
    direction: Direction = "OUT"

class Aggregation(BaseModel):
    function: Literal["count"]
    variable: Literal["w"] 
    alias: str

class OrderBy(BaseModel):
    field: str
    direction: Literal["ASC", "DESC"] = "DESC"

class Filter(BaseModel):
    field: str
    op: Literal["=", ">", "<"]
    value: str | int

class CypherQueryPlan(BaseModel):
    match: MatchPattern
    aggregations: List[Aggregation] = []
    return_fields: List[str]
    order_by: Optional[OrderBy] = None
    limit: Optional[int] = None
```

### Configuration Schema
```python
@dataclass
class Config:
    db_uri: str
    db_user: str  
    db_password: str
    target_db: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Environment variable loading consistency
*For any* valid .env file, loading environment variables should result in all required configuration values being accessible through the ConfigManager
**Validates: Requirements 3.1**

Property 2: Missing environment variable error handling
*For any* missing required environment variable, the script should display an informative error message and exit gracefully
**Validates: Requirements 3.2**

Property 3: Connection parameter validation
*For any* invalid AWS or Neo4j connection parameters, the validation should fail with descriptive error messages before attempting connections
**Validates: Requirements 3.3**

Property 4: Database connection error handling
*For any* database connection failure, the script should handle the error gracefully and provide clear feedback to the user
**Validates: Requirements 3.4, 4.4**

Property 5: Cypher validation preservation
*For any* Cypher query, all validation functions from the original notebook should produce identical results in the script
**Validates: Requirements 4.2, 4.3**

Property 6: Database connection cleanup
*For any* database operation, connections should be properly closed regardless of success or failure
**Validates: Requirements 4.5**

Property 7: Command line argument processing
*For any* valid command line arguments, the script should parse and process them correctly according to the defined interface
**Validates: Requirements 2.1**

Property 8: Interactive mode operation modes
*For any* execution mode (single query or interactive), the script should support both modes and switch between them correctly
**Validates: Requirements 2.4**

Property 9: Query execution through agent
*For any* user query, the script should process it through the Strands agent and return results in the same format as the original notebook
**Validates: Requirements 6.1, 1.5**

Property 10: Error message consistency
*For any* error condition, the script should provide informative error messages that help users understand and resolve issues
**Validates: Requirements 7.1**

Property 11: Input validation before processing
*For any* user input, the script should validate parameters before processing to prevent invalid operations
**Validates: Requirements 7.3**

Property 12: Exit code appropriateness
*For any* execution scenario, the script should exit with appropriate status codes (0 for success, non-zero for errors)
**Validates: Requirements 7.5**

Property 13: Interactive session state persistence
*For any* sequence of queries in interactive mode, the agent state should persist between queries within the same session
**Validates: Requirements 8.4**

Property 14: Cypher safety preservation
*For any* Cypher query, all safety checks and validation from the original notebook should be preserved and function identically
**Validates: Requirements 6.5**

## Error Handling

The script implements comprehensive error handling at multiple levels:

### Configuration Errors
- Missing .env file
- Invalid environment variables
- Missing required configuration values

### Connection Errors  
- AWS Bedrock authentication failures
- Neo4j database connection issues
- Network connectivity problems

### Query Processing Errors
- Invalid Cypher syntax
- Forbidden Cypher operations
- Empty result sets
- Agent processing failures

### User Interface Errors
- Invalid command line arguments
- Keyboard interrupts (Ctrl+C)
- Interactive mode exit conditions

## Testing Strategy

The testing approach combines unit tests for individual components and integration tests for end-to-end functionality:

### Unit Tests
- Configuration loading and validation
- Cypher validation functions
- Neo4j client operations
- CLI argument parsing
- Error handling scenarios

### Property-Based Tests
- Environment variable loading with various .env configurations
- Cypher validation with generated query inputs
- Connection handling with simulated failures
- Command line argument processing with random inputs
- Interactive mode state management across query sequences

### Integration Tests
- End-to-end query processing
- AWS Bedrock integration
- Neo4j database operations
- CLI interface functionality
- Error propagation through the system

Each property-based test will run a minimum of 100 iterations to ensure comprehensive coverage through randomization. Tests will be tagged with the format: **Feature: notebook-to-script-conversion, Property {number}: {property_text}**
