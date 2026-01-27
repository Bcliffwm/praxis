"""
Base research query agent implementation.

Provides core functionality for querying Neo4j database using
AWS Bedrock and Strands agents framework.
"""

import logging
from typing import Dict, List, Any, Optional
import boto3
from strands import Agent, tool
from strands.models import BedrockModel

from ..core.config import ConfigManager
from ..core.database import Neo4jClient
from ..utils.validators import CypherValidator
from ..utils.exceptions import GraphRAGError, ValidationError

logger = logging.getLogger(__name__)


class ResearchQueryAgent:
    """Base research query agent that integrates Strands with Neo4j for research queries."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the Research Query Agent.
        
        Args:
            config_manager: ConfigManager instance with loaded configuration
        """
        self.config_manager = config_manager
        self.bedrock_model = None
        self.neo4j_tool = None
        self.agent = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components (Bedrock model, Neo4j client, and Agent)."""
        logger.info("Initializing Research Query Agent components")
        self.bedrock_model = self.initialize_bedrock_model()
        self.neo4j_tool = self.create_neo4j_tool()
        self.agent = self.setup_agent()
        logger.info("Research Query Agent initialized successfully")
    
    def initialize_bedrock_model(self) -> BedrockModel:
        """Initialize BedrockModel with correct parameters."""
        try:
            aws_config = self.config_manager.get_aws_config()
            session = self._create_aws_session(aws_config)
            
            bedrock_model = BedrockModel(
                model_id='anthropic.claude-3-5-sonnet-20240620-v1:0',
                temperature=0.0,
                # Note: session parameter may cause warnings in some versions
                **({'session': session} if session else {})
            )
            
            logger.info("Bedrock model initialized successfully")
            return bedrock_model
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock model: {e}")
            raise GraphRAGError(f"Failed to initialize Bedrock model: {e}")
    
    def _create_aws_session(self, aws_config: Dict[str, str]) -> Optional[boto3.Session]:
        """Create AWS session with error handling."""
        try:
            required_keys = ['aws_access_key_id', 'aws_secret_access_key', 'region_name']
            for key in required_keys:
                if not aws_config.get(key):
                    raise ValueError(f"Missing AWS configuration: {key}")
            
            session = boto3.Session(
                aws_access_key_id=aws_config['aws_access_key_id'],
                aws_secret_access_key=aws_config['aws_secret_access_key'],
                region_name=aws_config['region_name']
            )
            
            # Test the session
            try:
                bedrock_client = session.client('bedrock-runtime')
                if not bedrock_client:
                    raise ValueError("Failed to create Bedrock client")
            except Exception as client_error:
                self._handle_aws_client_error(client_error, aws_config)
            
            logger.debug("AWS session created successfully")
            return session
            
        except Exception as e:
            logger.error(f"AWS session creation failed: {e}")
            raise GraphRAGError(f"AWS session creation failed: {e}")
    
    def _handle_aws_client_error(self, error: Exception, aws_config: Dict[str, str]):
        """Handle specific AWS client errors with helpful messages."""
        error_msg = str(error)
        
        if 'InvalidAccessKeyId' in error_msg:
            raise GraphRAGError(
                f"Invalid AWS Access Key ID: '{aws_config['aws_access_key_id']}'.\n"
                f"Please check your AWS credentials."
            )
        elif 'SignatureDoesNotMatch' in error_msg:
            raise GraphRAGError(
                "Invalid AWS Secret Access Key. Please verify your credentials."
            )
        elif 'UnauthorizedOperation' in error_msg:
            raise GraphRAGError(
                "AWS credentials do not have permission to access Bedrock service."
            )
        else:
            raise GraphRAGError(f"AWS authentication failed: {error_msg}")
    
    def create_neo4j_tool(self):
        """Create neo4j_query_tool with validation."""
        neo4j_config = self.config_manager.get_neo4j_config()
        
        @tool(
            name="neo4j_query_tool",
            description="Execute a READ-ONLY Cypher query against Neo4j"
        )
        def neo4j_query_tool(cypher: str, **kwargs) -> dict:
            """Execute a validated Cypher query against Neo4j."""
            try:
                # Validate and prepare the Cypher query
                safe_cypher = CypherValidator.prepare_cypher(cypher)
                CypherValidator.validate_properties(safe_cypher)
            except Exception as e:
                logger.warning(f"Cypher validation failed: {e}")
                return {
                    "error": "cypher_validation_error",
                    "message": str(e),
                    "original_cypher": cypher
                }
            
            # Create Neo4j client for this query
            try:
                with Neo4jClient(
                    uri=neo4j_config['uri'],
                    auth=neo4j_config['auth'],
                    database=neo4j_config['database']
                ) as client:
                    # Execute the query with parameters
                    params = {k: v for k, v in kwargs.items() if k != 'cypher'}
                    records = client.run_cypher(safe_cypher, params)
                    
                    return {
                        "row_count": len(records),
                        "records": records,
                        "query_parameters": params
                    }
                    
            except GraphRAGError as e:
                logger.error(f"Neo4j query execution failed: {e}")
                return {
                    "error": "query_execution_error",
                    "message": str(e),
                    "cypher": safe_cypher
                }
            except Exception as e:
                logger.error(f"Unexpected error during query execution: {e}")
                return {
                    "error": "unexpected_error",
                    "message": f"Unexpected error: {e}",
                    "cypher": safe_cypher
                }
        
        return neo4j_query_tool
    
    def setup_agent(self) -> Agent:
        """Set up Agent with system prompt."""
        system_prompt = """
You are an assistant that can query a Neo4j database containing academic research data.

Database Schema:
- Author nodes: Researchers and academics with properties (id, name, cited_by_count, works_count)
- Work nodes: Academic papers and publications with properties (id, title, type, publication_date)
- Topic nodes: Research topics with properties (id, topic_name, description)

Relationships:
- WORK_AUTHORED_BY: Author -> Work (authors write works)
- WORK_HAS_TOPIC: Work -> Topic (works are associated with topics)
- RELATED_TO: Work -> Work (works are related to each other)

Rules:
- Call the tool `neo4j_query_tool` when data is required
- Only generate READ-ONLY Cypher queries
- Never use CREATE, MERGE, DELETE, SET, DROP, CALL, or APOC procedures
- Use proper Cypher syntax with correct node labels and relationship types
- Include appropriate WHERE clauses and LIMIT statements
- Provide clear explanations of query results

When querying:
1. Use MATCH patterns to find nodes and relationships
2. Use WHERE clauses for filtering
3. Use RETURN to specify what data to retrieve
4. Use ORDER BY and LIMIT for result organization
5. Explain the relationships and patterns found in the data
        """
        
        agent = Agent(
            model=self.bedrock_model,
            tools=[self.neo4j_tool],
            system_prompt=system_prompt.strip()
        )
        
        logger.debug("Agent setup completed")
        return agent
    
    def query(self, question: str) -> str:
        """Process a query through the Strands agent.
        
        Args:
            question: User question/query
            
        Returns:
            Agent response as string
            
        Raises:
            GraphRAGError: If agent is not initialized or query processing fails
        """
        if not self.agent:
            raise GraphRAGError("Agent not initialized")
        
        try:
            # Validate input
            if not question or not question.strip():
                raise ValidationError("Query cannot be empty")
            
            logger.info(f"Processing query: {question[:100]}...")
            response = self.agent(question.strip())
            logger.info("Query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise GraphRAGError(f"Query processing failed: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the connected database."""
        try:
            neo4j_config = self.config_manager.get_neo4j_config()
            with Neo4jClient(
                uri=neo4j_config['uri'],
                auth=neo4j_config['auth'],
                database=neo4j_config['database']
            ) as client:
                return client.get_database_info()
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the database connection."""
        try:
            neo4j_config = self.config_manager.get_neo4j_config()
            with Neo4jClient(
                uri=neo4j_config['uri'],
                auth=neo4j_config['auth'],
                database=neo4j_config['database']
            ) as client:
                # Simple test query
                result = client.run_cypher("RETURN 1 as test")
                return {
                    "status": "success",
                    "message": "Database connection successful",
                    "test_result": result
                }
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def close(self) -> None:
        """Clean up resources."""
        # Note: Individual Neo4j clients are closed after each query
        # No persistent connections to clean up
        logger.debug("Research Query Agent resources cleaned up")
        pass