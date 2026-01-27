# Implementation Plan: Notebook to Script Conversion

## Overview

Convert bedrock_strands.ipynb to a standalone Python script with CLI interface, maintaining all functionality while adding proper error handling, configuration management, and both single-query and interactive modes.

## Tasks

- [x] 1. Set up project structure and core configuration
  - Create research_query_agent.py file
  - Implement ConfigManager class for environment variable handling
  - Add proper imports and module organization
  - _Requirements: 1.1, 1.2, 3.1_

- [x] 1.1 Write property test for environment variable loading
  - **Property 1: Environment variable loading consistency**
  - **Validates: Requirements 3.1**

- [x] 2. Implement Neo4j database layer
  - [x] 2.1 Create Neo4jClient class with connection management
    - Port Neo4jClient class from notebook
    - Add proper connection handling and cleanup
    - _Requirements: 4.1, 4.5_

  - [x] 2.2 Write property test for database connection cleanup
    - **Property 6: Database connection cleanup**
    - **Validates: Requirements 4.5**

  - [x] 2.3 Implement Cypher validation system
    - Port all validation functions (assert_read_only, validate_properties, etc.)
    - Maintain schema definitions and property aliases
    - _Requirements: 4.2, 4.3_

  - [x] 2.4 Write property test for Cypher validation preservation
    - **Property 5: Cypher validation preservation**
    - **Validates: Requirements 4.2, 4.3**

- [x] 3. Create Strands agent integration
  - [x] 3.1 Implement ResearchQueryAgent class
    - Initialize BedrockModel with correct parameters
    - Create neo4j_query_tool with validation
    - Set up Agent with system prompt
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 3.2 Write unit tests for agent initialization
    - Test BedrockModel initialization
    - Test Agent creation with correct tools
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 3.3 Add AWS connection handling
    - Implement AWS session creation
    - Add error handling for authentication issues
    - _Requirements: 5.4, 5.5_

  - [x] 3.4 Write property test for AWS connection error handling
    - **Property 3: Connection parameter validation**
    - **Validates: Requirements 5.5**

- [x] 4. Checkpoint - Ensure core functionality works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement CLI interface
  - [x] 5.1 Create CLIInterface class with argument parsing
    - Add argparse configuration for command line options
    - Support both query argument and interactive mode
    - _Requirements: 2.1, 2.2_

  - [x] 5.2 Write property test for command line argument processing
    - **Property 7: Command line argument processing**
    - **Validates: Requirements 2.1**

  - [x] 5.3 Implement single query execution mode
    - Process single query from command line
    - Format and display results
    - _Requirements: 2.4, 6.2_

  - [x] 5.4 Write unit test for help text display
    - Test help text is shown when requested
    - _Requirements: 2.2_

- [x] 6. Add interactive mode functionality
  - [x] 6.1 Implement interactive query loop
    - Continuous prompt for user queries
    - Handle exit commands and keyboard interrupts
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [x] 6.2 Write property test for interactive session state persistence
    - **Property 13: Interactive session state persistence**
    - **Validates: Requirements 8.4**

  - [x] 6.3 Add graceful error handling in interactive mode
    - Handle query errors without exiting
    - Maintain session state across errors
    - _Requirements: 8.4_

  - [x] 6.4 Write unit test for keyboard interrupt handling
    - Test Ctrl+C handling in interactive mode
    - _Requirements: 8.5_

- [x] 7. Implement comprehensive error handling
  - [x] 7.1 Add configuration validation and error messages
    - Validate all required environment variables
    - Provide helpful error messages for missing config
    - _Requirements: 3.2, 3.3_

  - [x] 7.2 Write property test for missing environment variable handling
    - **Property 2: Missing environment variable error handling**
    - **Validates: Requirements 3.2**

  - [x] 7.3 Add database and AWS connection error handling
    - Handle connection failures gracefully
    - Provide clear feedback for connection issues
    - _Requirements: 3.4, 4.4_

  - [x] 7.4 Write property test for database connection error handling
    - **Property 4: Database connection error handling**
    - **Validates: Requirements 3.4, 4.4**

  - [x] 7.5 Implement input validation and logging
    - Validate user inputs before processing
    - Add logging for debugging purposes
    - Set appropriate exit codes
    - _Requirements: 7.3, 7.4, 7.5_

  - [x] 7.6 Write property test for input validation
    - **Property 11: Input validation before processing**
    - **Validates: Requirements 7.3**

- [x] 8. Add query processing and result formatting
  - [x] 8.1 Implement query execution through agent
    - Process queries using Strands agent
    - Maintain functionality equivalence with notebook
    - _Requirements: 6.1, 1.5_

  - [x] 8.2 Write property test for query execution consistency
    - **Property 9: Query execution through agent**
    - **Validates: Requirements 6.1, 1.5**

  - [x] 8.3 Add result formatting and display
    - Format query results for readability
    - Handle both successful results and errors
    - Handle empty result sets
    - _Requirements: 6.2, 6.3, 6.4_

  - [x] 8.4 Write unit test for empty result set handling
    - Test graceful handling of queries with no results
    - _Requirements: 6.4_

- [x] 9. Preserve all Cypher safety features
  - [x] 9.1 Ensure all validation functions are preserved
    - Verify forbidden keyword checking
    - Maintain property and relationship normalization
    - _Requirements: 6.5_

  - [x] 9.2 Write property test for Cypher safety preservation
    - **Property 14: Cypher safety preservation**
    - **Validates: Requirements 6.5**

- [x] 10. Final integration and testing
  - [x] 10.1 Create main execution function
    - Wire all components together
    - Add proper script entry point
    - _Requirements: All requirements_

  - [x] 10.2 Write property test for exit code appropriateness
    - **Property 12: Exit code appropriateness**
    - **Validates: Requirements 7.5**

  - [x] 10.3 Add comprehensive error message testing
    - Verify informative error messages for common issues
    - Test error propagation through all layers
    - _Requirements: 7.1_

  - [x] 10.4 Write property test for error message consistency
    - **Property 10: Error message consistency**
    - **Validates: Requirements 7.1**

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases