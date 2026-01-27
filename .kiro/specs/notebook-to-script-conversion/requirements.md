# Requirements Document

## Introduction

Convert the bedrock_strands.ipynb Jupyter notebook into a standalone Python script that can be executed from the command line. The script should maintain all functionality while adding proper CLI interface, error handling, and configuration management.

## Glossary

- **Strands Agent**: AI agent framework for research analysis tasks using AWS Bedrock
- **Neo4j Client**: Database client for executing Cypher queries against Neo4j graph database
- **Cypher Query Tool**: Strands tool that validates and executes read-only Cypher queries
- **CLI**: Command Line Interface for script execution
- **Environment Configuration**: AWS and Neo4j connection settings from .env file

## Requirements

### Requirement 1: Script Structure and Organization

**User Story:** As a developer, I want the notebook converted to a well-structured Python script, so that I can run it from the command line and maintain it easily.

#### Acceptance Criteria

1. THE Script SHALL be organized into logical functions and classes
2. THE Script SHALL import all necessary dependencies at the top
3. THE Script SHALL follow Python best practices for code organization
4. THE Script SHALL include proper docstrings for all functions and classes
5. THE Script SHALL maintain the same functionality as the original notebook

### Requirement 2: Command Line Interface

**User Story:** As a user, I want to run the script from the command line with different options, so that I can interact with the Neo4j database through the Strands agent.

#### Acceptance Criteria

1. THE Script SHALL accept command line arguments for user queries
2. THE Script SHALL provide help text explaining available options
3. WHEN no query is provided, THE Script SHALL prompt for interactive input
4. THE Script SHALL support both single query execution and interactive mode
5. THE Script SHALL display results in a readable format

### Requirement 3: Environment Configuration

**User Story:** As a user, I want the script to automatically load environment variables, so that I don't need to manually configure database and AWS connections.

#### Acceptance Criteria

1. THE Script SHALL load environment variables from .env file
2. WHEN required environment variables are missing, THE Script SHALL display helpful error messages
3. THE Script SHALL validate AWS and Neo4j connection parameters
4. THE Script SHALL provide clear feedback when connections fail

### Requirement 4: Neo4j Client Integration

**User Story:** As a developer, I want the Neo4j client functionality preserved, so that the script can execute validated Cypher queries against the graph database.

#### Acceptance Criteria

1. THE Script SHALL include the Neo4jClient class with all methods
2. THE Script SHALL maintain all Cypher validation functions
3. THE Script SHALL preserve schema validation and property normalization
4. THE Script SHALL handle database connection errors gracefully
5. THE Script SHALL close database connections properly

### Requirement 5: Strands Agent Configuration

**User Story:** As a user, I want the Strands agent properly configured, so that I can query the Neo4j database using natural language through AWS Bedrock.

#### Acceptance Criteria

1. THE Script SHALL initialize the BedrockModel with correct parameters
2. THE Script SHALL create the Agent with neo4j_query_tool
3. THE Script SHALL preserve the system prompt for database querying
4. THE Script SHALL handle AWS Bedrock authentication and connection
5. THE Script SHALL provide meaningful error messages for AWS connection issues

### Requirement 6: Query Processing and Results

**User Story:** As a user, I want to see query results in a clear format, so that I can understand the information retrieved from the database.

#### Acceptance Criteria

1. THE Script SHALL execute user queries through the Strands agent
2. THE Script SHALL display query results in a formatted, readable manner
3. THE Script SHALL show both successful results and error messages clearly
4. THE Script SHALL handle empty result sets gracefully
5. THE Script SHALL preserve all Cypher query validation and safety checks

### Requirement 7: Error Handling and Logging

**User Story:** As a user, I want clear error messages and logging, so that I can troubleshoot issues when they occur.

#### Acceptance Criteria

1. THE Script SHALL provide informative error messages for common issues
2. THE Script SHALL handle network connectivity problems gracefully
3. THE Script SHALL validate input parameters before processing
4. THE Script SHALL log important operations for debugging
5. THE Script SHALL exit with appropriate status codes

### Requirement 8: Interactive Mode

**User Story:** As a user, I want an interactive mode, so that I can ask multiple queries without restarting the script.

#### Acceptance Criteria

1. WHEN run without arguments, THE Script SHALL enter interactive mode
2. THE Script SHALL prompt for queries continuously until exit
3. THE Script SHALL provide commands to exit the interactive session
4. THE Script SHALL maintain agent state between queries in interactive mode
5. THE Script SHALL handle keyboard interrupts gracefully