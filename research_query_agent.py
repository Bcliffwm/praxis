#!/usr/bin/env python3
"""
Research Query Agent - Notebook to Script Conversion

Converts bedrock_strands.ipynb functionality into a standalone Python script
with CLI interface, maintaining all functionality while adding proper error
handling, configuration management, and both single-query and interactive modes.
"""

import os
import re
import sys
import argparse
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Literal, Optional
from dotenv import load_dotenv

# Third-party imports
import boto3
from neo4j import GraphDatabase
from pydantic import BaseModel

# Strands imports
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import current_time


def setup_logging(level: str = 'INFO') -> None:
    """Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure logging format
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level: {level}")


def validate_query_input(query: str) -> str:
    """Validate user query input before processing.
    
    Args:
        query: User query string
        
    Returns:
        Validated and sanitized query string
        
    Raises:
        ValueError: If query is invalid
    """
    logger = logging.getLogger(__name__)
    
    if not isinstance(query, str):
        logger.error(f"Invalid query type: {type(query)}. Expected string.")
        raise ValueError(f"Query must be a string, got {type(query)}")
    
    # Strip whitespace
    query = query.strip()
    
    # Check for empty query
    if not query:
        logger.warning("Empty query provided")
        raise ValueError("Query cannot be empty")
    
    # Check for excessively long queries (prevent potential DoS)
    max_query_length = 10000  # 10KB limit
    if len(query) > max_query_length:
        logger.warning(f"Query too long: {len(query)} characters (max: {max_query_length})")
        raise ValueError(f"Query too long. Maximum length is {max_query_length} characters, got {len(query)}")
    
    # Check for potentially dangerous patterns (basic security)
    dangerous_patterns = [
        r'<script[^>]*>',  # Script tags
        r'javascript:',    # JavaScript URLs
        r'data:text/html', # Data URLs with HTML
        r'vbscript:',      # VBScript URLs
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            logger.warning(f"Potentially dangerous pattern detected in query: {pattern}")
            raise ValueError("Query contains potentially dangerous content")
    
    # Log successful validation
    logger.debug(f"Query validated successfully: {len(query)} characters")
    
    return query


def validate_cli_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Raises:
        ValueError: If arguments are invalid
    """
    logger = logging.getLogger(__name__)
    
    # Validate query if provided
    if args.query is not None:
        try:
            validate_query_input(args.query)
            logger.debug("CLI query argument validated successfully")
        except ValueError as e:
            logger.error(f"Invalid CLI query argument: {e}")
            raise ValueError(f"Invalid query argument: {e}")
    
    # Validate interactive flag (should be boolean)
    if not isinstance(args.interactive, bool):
        logger.error(f"Invalid interactive flag type: {type(args.interactive)}")
        raise ValueError(f"Interactive flag must be boolean, got {type(args.interactive)}")
    
    # Log successful validation
    logger.info(f"CLI arguments validated: query={'provided' if args.query else 'none'}, interactive={args.interactive}")


@dataclass
class Config:
    """Configuration data class for environment variables."""
    db_uri: str
    db_user: str
    db_password: str
    target_db: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str


class ConfigManager:
    """Manages environment variable loading and validation."""
    
    def __init__(self):
        """Initialize ConfigManager and load configuration."""
        self.config: Optional[Config] = None
        self.load_environment()
        self.validate_config()
    
    def load_environment(self) -> None:
        """Load environment variables from .env file."""
        # Try to load .env file
        env_file_loaded = load_dotenv()
        
        # Load configuration from environment variables
        try:
            self.config = Config(
                db_uri=os.getenv('DB_URI', '').strip("'\""),
                db_user=os.getenv('DB_USER', ''),
                db_password=os.getenv('DB_PASSWORD', ''),
                target_db=os.getenv('TARGET_DB', ''),
                aws_access_key_id=os.getenv('aws_access_key_id', ''),
                aws_secret_access_key=os.getenv('aws_secret_access_key', ''),
                region_name=os.getenv('region_name', '').strip()
            )
        except Exception as e:
            error_message = f"Failed to load environment configuration: {e}"
            if not env_file_loaded:
                error_message += "\n\nNote: No .env file found. You can either:"
                error_message += "\n- Create a .env file in the project root with required variables"
                error_message += "\n- Set environment variables directly in your system"
            raise ValueError(error_message)
    
    def validate_config(self) -> None:
        """Validate that all required configuration values are present and properly formatted."""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        required_fields = [
            ('db_uri', 'DB_URI'),
            ('db_user', 'DB_USER'),
            ('db_password', 'DB_PASSWORD'),
            ('target_db', 'TARGET_DB'),
            ('aws_access_key_id', 'aws_access_key_id'),
            ('aws_secret_access_key', 'aws_secret_access_key'),
            ('region_name', 'region_name')
        ]
        
        missing_fields = []
        invalid_fields = []
        
        for field_name, env_var_name in required_fields:
            value = getattr(self.config, field_name)
            if not value:
                missing_fields.append(env_var_name)
            else:
                # Validate specific field formats
                validation_error = self._validate_field_format(field_name, value, env_var_name)
                if validation_error:
                    invalid_fields.append(validation_error)
        
        # Collect all validation errors
        error_messages = []
        
        if missing_fields:
            error_messages.append(
                f"Missing required environment variables: {', '.join(missing_fields)}"
            )
        
        if invalid_fields:
            error_messages.extend(invalid_fields)
        
        if error_messages:
            error_message = ". ".join(error_messages)
            error_message += ".\n\nTroubleshooting tips:\n"
            error_message += "- Create a .env file in the project root directory\n"
            error_message += "- Ensure all required environment variables are set\n"
            error_message += "- Check that Neo4j URI format is correct (e.g., bolt://localhost:7687)\n"
            error_message += "- Verify AWS credentials are valid and have proper permissions\n"
            error_message += "- Confirm AWS region supports Bedrock service"
            
            raise ValueError(error_message)
    
    def _validate_field_format(self, field_name: str, value: str, env_var_name: str) -> Optional[str]:
        """Validate the format of specific configuration fields.
        
        Args:
            field_name: Name of the configuration field
            value: Value to validate
            env_var_name: Environment variable name for error messages
            
        Returns:
            Error message if validation fails, None if valid
        """
        if field_name == 'db_uri':
            # Validate Neo4j URI format
            if not (value.startswith('bolt://') or value.startswith('neo4j://') or value.startswith('bolt+s://') or value.startswith('neo4j+s://')):
                return f"Invalid Neo4j URI format for {env_var_name}: '{value}'. Expected format: bolt://host:port or neo4j://host:port"
        
        elif field_name == 'aws_access_key_id':
            # Validate AWS Access Key ID format (should start with AKIA or ASIA and be 20 characters)
            if not (value.startswith(('AKIA', 'ASIA')) and len(value) == 20):
                return f"Invalid AWS Access Key ID format for {env_var_name}: '{value}'. Expected format: 20-character string starting with AKIA or ASIA"
        
        elif field_name == 'aws_secret_access_key':
            # Validate AWS Secret Access Key format (should be 40 characters)
            if len(value) != 40:
                return f"Invalid AWS Secret Access Key format for {env_var_name}: Secret key should be 40 characters long"
        
        elif field_name == 'region_name':
            # Validate AWS region format
            import re
            if not re.match(r'^[a-z]{2}-[a-z]+-\d+$', value):
                return f"Invalid AWS region format for {env_var_name}: '{value}'. Expected format: us-east-1, eu-west-1, etc."
        
        elif field_name in ['db_user', 'db_password', 'target_db']:
            # Basic validation for database fields - ensure they're not just whitespace
            if not value.strip():
                return f"Invalid value for {env_var_name}: Cannot be empty or whitespace only"
        
        return None
    
    def get_neo4j_config(self) -> dict:
        """Get Neo4j connection configuration."""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        return {
            'uri': self.config.db_uri,
            'auth': (self.config.db_user, self.config.db_password),
            'database': self.config.target_db
        }
    
    def get_aws_config(self) -> dict:
        """Get AWS connection configuration."""
        if not self.config:
            raise ValueError("Configuration not loaded")
        
        return {
            'aws_access_key_id': self.config.aws_access_key_id,
            'aws_secret_access_key': self.config.aws_secret_access_key,
            'region_name': self.config.region_name
        }


class Neo4jClient:
    """Neo4j database client with connection management."""
    
    def __init__(self, uri: str, auth: tuple, database: str):
        """Initialize Neo4j client with connection parameters.
        
        Args:
            uri: Neo4j database URI
            auth: Authentication tuple (username, password)
            database: Target database name
            
        Raises:
            ValueError: If connection parameters are invalid or connection fails
        """
        self.database = database  # Set database name first for error handling
        
        try:
            self.driver = GraphDatabase.driver(uri=uri, auth=auth)
            
            # Test the connection by attempting to verify connectivity
            self._test_connection()
            
        except Exception as e:
            # Handle specific Neo4j connection errors
            error_message = self._format_connection_error(e, uri, auth[0])
            raise ValueError(error_message)
    
    def _test_connection(self) -> None:
        """Test the database connection to ensure it's working.
        
        Raises:
            Exception: If connection test fails
        """
        try:
            with self.driver.session(database=self.database) as session:
                # Simple query to test connectivity
                session.run("RETURN 1 AS test")
        except Exception as e:
            # Re-raise the exception to be handled by the caller
            raise e
    
    def _format_connection_error(self, error: Exception, uri: str, username: str) -> str:
        """Format connection errors with helpful messages.
        
        Args:
            error: The original exception
            uri: Neo4j URI that failed
            username: Username used for authentication
            
        Returns:
            Formatted error message with troubleshooting tips
        """
        error_str = str(error).lower()
        
        if 'connection refused' in error_str or 'failed to establish connection' in error_str:
            return (
                f"Failed to connect to Neo4j database at '{uri}'. "
                f"Connection refused.\n\n"
                f"Troubleshooting tips:\n"
                f"- Ensure Neo4j database is running\n"
                f"- Check that the URI '{uri}' is correct\n"
                f"- Verify the port is accessible and not blocked by firewall\n"
                f"- For local installations, try 'bolt://localhost:7687'"
            )
        elif 'authentication failed' in error_str or 'unauthorized' in error_str:
            return (
                f"Authentication failed for Neo4j database at '{uri}' with username '{username}'.\n\n"
                f"Troubleshooting tips:\n"
                f"- Check that the username and password are correct\n"
                f"- Verify the user has access to the database\n"
                f"- For default installations, try username 'neo4j' with your set password"
            )
        elif 'database does not exist' in error_str or 'unknown database' in error_str:
            return (
                f"Database '{self.database}' does not exist on Neo4j server at '{uri}'.\n\n"
                f"Troubleshooting tips:\n"
                f"- Check that the database name is correct\n"
                f"- Create the database if it doesn't exist\n"
                f"- For default installations, try database name 'neo4j'"
            )
        elif 'timeout' in error_str:
            return (
                f"Connection to Neo4j database at '{uri}' timed out.\n\n"
                f"Troubleshooting tips:\n"
                f"- Check network connectivity to the database server\n"
                f"- Verify the server is responding and not overloaded\n"
                f"- Try increasing connection timeout settings"
            )
        else:
            return (
                f"Failed to connect to Neo4j database at '{uri}': {error}\n\n"
                f"Troubleshooting tips:\n"
                f"- Check that Neo4j database is running and accessible\n"
                f"- Verify connection parameters (URI, username, password, database)\n"
                f"- Check network connectivity and firewall settings"
            )
    
    def close(self) -> None:
        """Close the database connection."""
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                # Ignore errors during cleanup
                pass
    
    def run_cypher(self, query: str, params: Dict[str, Any] | None = None) -> List[Dict]:
        """Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            params: Optional query parameters
            
        Returns:
            List of dictionaries containing query results
            
        Raises:
            ValueError: If query execution fails
        """
        try:
            with self.driver.session(database=self.database) as session:
                print(query)  # Adding for LLM visibility (preserved from notebook)
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except Exception as e:
            # Format query execution errors
            error_message = self._format_query_error(e, query)
            raise ValueError(error_message)
    
    def _format_query_error(self, error: Exception, query: str) -> str:
        """Format query execution errors with helpful messages.
        
        Args:
            error: The original exception
            query: The query that failed
            
        Returns:
            Formatted error message
        """
        error_str = str(error).lower()
        
        if 'syntax error' in error_str or 'invalid syntax' in error_str:
            return f"Cypher syntax error in query: {error}\n\nQuery: {query}"
        elif 'constraint' in error_str or 'violation' in error_str:
            return f"Database constraint violation: {error}\n\nQuery: {query}"
        elif 'timeout' in error_str:
            return f"Query execution timed out: {error}\n\nQuery: {query}"
        elif 'memory' in error_str or 'out of memory' in error_str:
            return f"Query exceeded memory limits: {error}\n\nQuery: {query}"
        else:
            return f"Query execution failed: {error}\n\nQuery: {query}"


# Cypher Validation System
FORBIDDEN_KEYWORDS = {
    "CREATE", "MERGE", "DELETE", "SET", "DROP",
    "REMOVE", "CALL", "LOAD CSV", "APOC"
}

SCHEMA = {
    "Author": {
        "id",
        "name",
        "display_name"
    },
    "Work": {
        "id",
        "title",
        "type",
        "publication_date"   # ✅ canonical
    },
    "Topic": {
        "id",
        "display_name",
        "score"
    }
}

PROPERTY_ALIASES = {
    "publication_year": "publication_date",
    "pub_year": "publication_date",
    "year": "publication_date"
}

RELATIONSHIP_CANONICAL = {
    "WROTE": "WORK_AUTHORED_BY",
    "AUTHORED": "WORK_AUTHORED_BY",
    "AUTHORED_BY": "WORK_AUTHORED_BY",
    "HAS_TOPIC": "WORK_HAS_TOPIC",
    "TOPIC_IN": "WORK_HAS_TOPIC"
}

VALID_LABELS = {"Author", "Work", "Topic"}

VALID_NODE_LABELS = {"Author", "Work", "Topic"}
VALID_RELATIONSHIPS = {
    "WORK_AUTHORED_BY": {
        "from": "Author",
        "to": "Work",
        "direction": "OUT"
    },
    "WORK_HAS_TOPIC": {
        "from": "Work",
        "to": "Topic",
        "direction": "OUT"
    }
}


class CypherValidator:
    """Cypher query validation system."""
    
    @staticmethod
    def assert_read_only(cypher: str) -> None:
        """Ensure query contains only read-only operations.
        
        Args:
            cypher: Cypher query string
            
        Raises:
            ValueError: If forbidden keywords are found
        """
        upper = cypher.upper()
        for kw in FORBIDDEN_KEYWORDS:
            if kw in upper:
                raise ValueError(f"Forbidden Cypher keyword: {kw}")
    
    @staticmethod
    def validate_properties(cypher: str) -> None:
        """Validate that all referenced properties exist in schema.
        
        Args:
            cypher: Cypher query string
            
        Raises:
            ValueError: If unknown properties are referenced
        """
        matches = re.findall(r"(\w+)\.(\w+)", cypher)
        
        for var, prop in matches:
            # we can't reliably infer labels from vars,
            # so we check against ALL known properties
            if not any(prop in props for props in SCHEMA.values()):
                raise ValueError(
                    f"Unknown property `{prop}` referenced in Cypher."
                )
    
    @staticmethod
    def normalize_properties(cypher: str) -> str:
        """Replace known hallucinated property names with canonical ones.
        
        Args:
            cypher: Cypher query string
            
        Returns:
            Normalized Cypher query string
        """
        for bad, good in PROPERTY_ALIASES.items():
            # match `.publication_year` safely
            cypher = re.sub(
                rf"\.{bad}\b",
                f".{good}",
                cypher
            )
        return cypher
    
    @staticmethod
    def normalize_relationships(cypher: str) -> str:
        """Replace relationship aliases with canonical names.
        
        Args:
            cypher: Cypher query string
            
        Returns:
            Normalized Cypher query string
        """
        for bad, good in RELATIONSHIP_CANONICAL.items():
            cypher = cypher.replace(f":{bad}", f":{good}")
        return cypher
    
    @staticmethod
    def validate_labels(cypher: str) -> None:
        """Validate that all labels and relationships are known.
        
        Args:
            cypher: Cypher query string
            
        Raises:
            ValueError: If unknown labels or relationships are found
        """
        labels = re.findall(r":([A-Za-z_][A-Za-z0-9_]*)", cypher)
        for label in labels:
            if label not in VALID_LABELS and label not in RELATIONSHIP_CANONICAL.values():
                raise ValueError(f"Unknown label or relationship: {label}")
    
    @staticmethod
    def prepare_cypher(cypher: str) -> str:
        """Prepare and validate a Cypher query for execution.
        
        Args:
            cypher: Raw Cypher query string
            
        Returns:
            Validated and normalized Cypher query string
            
        Raises:
            ValueError: If validation fails
        """
        CypherValidator.assert_read_only(cypher)
        cypher = CypherValidator.normalize_relationships(cypher)
        CypherValidator.validate_labels(cypher)
        return cypher


# Pydantic Models for Strands (preserved from notebook)
AuthorLabel = Literal["Author"]
TopicLabel = Literal["Topic"]
RelationshipType = Literal["WORK_AUTHORED_BY"]
WorkLabel = Literal["Work"]
Direction = Literal["OUT"]


class MatchPattern(BaseModel):
    """Match pattern for Cypher queries."""
    start_label: AuthorLabel
    relationship: RelationshipType
    end_label: WorkLabel
    direction: Direction = "OUT"


class Aggregation(BaseModel):
    """Aggregation specification for Cypher queries."""
    function: Literal["count"]
    variable: Literal["w"]
    alias: str


class OrderBy(BaseModel):
    """Order by specification for Cypher queries."""
    field: str
    direction: Literal["ASC", "DESC"] = "DESC"


class Filter(BaseModel):
    """Filter specification for Cypher queries."""
    field: str
    op: Literal["=", ">", "<"]
    value: str | int


class CypherQueryPlan(BaseModel):
    """Complete Cypher query plan specification."""
    match: MatchPattern
    aggregations: List[Aggregation] = []
    return_fields: List[str]
    order_by: Optional[OrderBy] = None
    limit: Optional[int] = None


def render_cypher(plan: CypherQueryPlan) -> str:
    """Render a CypherQueryPlan into a Cypher query string.
    
    Args:
        plan: Query plan specification
        
    Returns:
        Rendered Cypher query string
    """
    m = plan.match

    rel = f"-[:{m.relationship}]->"

    match_clause = (
        f"MATCH (a:{m.start_label})"
        f"{rel}"
        f"(w:{m.end_label})"
    )

    returns = plan.return_fields.copy()

    for agg in plan.aggregations:
        returns.append(
            f"{agg.function.upper()}({agg.variable}) AS {agg.alias}"
        )

    return_clause = "RETURN " + ", ".join(returns)

    order_clause = ""
    if plan.order_by:
        order_clause = (
            f" ORDER BY {plan.order_by.field} "
            f"{plan.order_by.direction}"
        )

    limit_clause = f" LIMIT {plan.limit}" if plan.limit else ""

    return f"{match_clause} {return_clause}{order_clause}{limit_clause}"


class ResearchQueryAgent:
    """Research Query Agent that integrates Strands with Neo4j for research queries."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the Research Query Agent.
        
        Args:
            config_manager: ConfigManager instance with loaded configuration
        """
        self.config_manager = config_manager
        self.neo4j_client = None
        self.bedrock_model = None
        self.agent = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components (Bedrock model, Neo4j client, and Agent)."""
        self.bedrock_model = self.initialize_bedrock_model()
        self.neo4j_tool = self.create_neo4j_tool()
        self.agent = self.setup_agent()
    
    def initialize_bedrock_model(self) -> BedrockModel:
        """Initialize BedrockModel with correct parameters.
        
        Returns:
            Configured BedrockModel instance
            
        Raises:
            ValueError: If AWS configuration is invalid
        """
        try:
            aws_config = self.config_manager.get_aws_config()
            
            # Create and test AWS session with credentials
            session = self._create_aws_session(aws_config)
            
            # Initialize BedrockModel with the session
            bedrock_model = BedrockModel(
                model_id='anthropic.claude-3-5-sonnet-20240620-v1:0',
                temperature=0.0,
                session=session
            )
            
            return bedrock_model
            
        except Exception as e:
            raise ValueError(f"Failed to initialize Bedrock model: {e}")
    
    def _create_aws_session(self, aws_config: dict) -> boto3.Session:
        """Create AWS session with error handling for authentication issues.
        
        Args:
            aws_config: AWS configuration dictionary
            
        Returns:
            Configured boto3.Session instance
            
        Raises:
            ValueError: If AWS authentication fails
        """
        try:
            # Validate AWS configuration parameters
            required_keys = ['aws_access_key_id', 'aws_secret_access_key', 'region_name']
            for key in required_keys:
                if not aws_config.get(key):
                    raise ValueError(f"Missing or empty AWS configuration: {key}")
            
            # Create AWS session with credentials
            session = boto3.Session(
                aws_access_key_id=aws_config['aws_access_key_id'],
                aws_secret_access_key=aws_config['aws_secret_access_key'],
                region_name=aws_config['region_name']
            )
            
            # Test the session by attempting to create a bedrock-runtime client
            # This will validate credentials and region without making actual API calls
            try:
                bedrock_client = session.client('bedrock-runtime')
                # Verify the client was created successfully
                if not bedrock_client:
                    raise ValueError("Failed to create Bedrock client")
            except Exception as client_error:
                # Handle specific AWS authentication errors
                error_msg = str(client_error)
                
                # Check for specific AWS error types
                if 'InvalidAccessKeyId' in error_msg:
                    raise ValueError(
                        f"Invalid AWS Access Key ID: '{aws_config['aws_access_key_id']}'.\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Check that your AWS Access Key ID is correct\n"
                        f"- Ensure the key is active and not disabled\n"
                        f"- Verify you're using the right AWS account credentials"
                    )
                elif 'SignatureDoesNotMatch' in error_msg:
                    raise ValueError(
                        f"Invalid AWS Secret Access Key.\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Check that your AWS Secret Access Key is correct\n"
                        f"- Ensure there are no extra spaces or characters\n"
                        f"- Verify the secret key matches the access key ID"
                    )
                elif 'TokenRefreshRequired' in error_msg:
                    raise ValueError(
                        f"AWS credentials have expired.\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Refresh your AWS credentials\n"
                        f"- Check if you're using temporary credentials that have expired\n"
                        f"- Update your .env file with new credentials"
                    )
                elif 'UnauthorizedOperation' in error_msg:
                    raise ValueError(
                        f"AWS credentials do not have permission to access Bedrock service.\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Ensure your AWS user/role has Bedrock permissions\n"
                        f"- Check IAM policies for bedrock:* permissions\n"
                        f"- Verify the account has access to Amazon Bedrock service"
                    )
                elif 'InvalidRegion' in error_msg or 'EndpointConnectionError' in error_msg:
                    raise ValueError(
                        f"Invalid AWS region '{aws_config['region_name']}' or region does not support Bedrock service.\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Check that the region name is correct (e.g., 'us-east-1', 'us-west-2')\n"
                        f"- Verify the region supports Amazon Bedrock service\n"
                        f"- Try using 'us-east-1' which commonly supports Bedrock"
                    )
                elif 'NoCredentialsError' in error_msg:
                    raise ValueError(
                        f"No AWS credentials found.\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Set AWS credentials in your .env file\n"
                        f"- Ensure aws_access_key_id and aws_secret_access_key are configured\n"
                        f"- Check that environment variables are loaded correctly"
                    )
                elif 'PartialCredentialsError' in error_msg:
                    raise ValueError(
                        f"Incomplete AWS credentials provided.\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Ensure both aws_access_key_id and aws_secret_access_key are set\n"
                        f"- Check that all required AWS configuration is present\n"
                        f"- Verify no credentials are empty or None"
                    )
                elif 'ConnectTimeoutError' in error_msg or 'ReadTimeoutError' in error_msg:
                    raise ValueError(
                        f"Connection to AWS services timed out.\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Check your internet connection\n"
                        f"- Verify network connectivity to AWS services\n"
                        f"- Check if corporate firewall is blocking AWS endpoints"
                    )
                else:
                    raise ValueError(
                        f"AWS authentication failed: {error_msg}\n\n"
                        f"Troubleshooting tips:\n"
                        f"- Verify all AWS credentials are correct\n"
                        f"- Check that the region supports Bedrock service\n"
                        f"- Ensure your AWS account has proper permissions\n"
                        f"- Try testing with AWS CLI: 'aws sts get-caller-identity'"
                    )
            
            return session
            
        except ValueError:
            # Re-raise ValueError exceptions as-is
            raise
        except Exception as e:
            # Handle any other unexpected errors
            raise ValueError(
                f"Unexpected error during AWS session creation: {e}\n\n"
                f"Troubleshooting tips:\n"
                f"- Check that all AWS configuration values are valid\n"
                f"- Verify network connectivity\n"
                f"- Try restarting the application"
            )
    
    def create_neo4j_tool(self) -> callable:
        """Create neo4j_query_tool with validation.
        
        Returns:
            Configured neo4j_query_tool function
        """
        neo4j_config = self.config_manager.get_neo4j_config()
        
        @tool(
            name="neo4j_query_tool",
            description="Execute a READ-ONLY Cypher query against Neo4j"
        )
        def neo4j_query_tool(cypher: str, **kwargs) -> dict:
            """Execute a validated Cypher query against Neo4j.
            
            Args:
                cypher: Cypher query string
                **kwargs: Additional parameters (unused)
                
            Returns:
                Dictionary containing query results or error information
            """
            try:
                # Validate and prepare the Cypher query
                safe_cypher = CypherValidator.prepare_cypher(cypher)
                CypherValidator.validate_properties(safe_cypher)
            except Exception as e:
                return {
                    "error": "cypher_validation_error",
                    "message": str(e),
                    "original_cypher": cypher
                }
            
            # Create Neo4j client for this query
            try:
                client = Neo4jClient(
                    uri=neo4j_config['uri'],
                    auth=neo4j_config['auth'],
                    database=neo4j_config['database']
                )
            except ValueError as e:
                # Connection error during client creation
                return {
                    "error": "database_connection_error",
                    "message": str(e),
                    "cypher": safe_cypher
                }
            
            try:
                # Execute the query
                records = client.run_cypher(safe_cypher)
                return {
                    "row_count": len(records),
                    "records": records
                }
            except ValueError as e:
                # Query execution error
                return {
                    "error": "query_execution_error",
                    "message": str(e),
                    "cypher": safe_cypher
                }
            except Exception as e:
                # Unexpected error
                return {
                    "error": "unexpected_error",
                    "message": f"Unexpected error during query execution: {e}",
                    "cypher": safe_cypher
                }
            finally:
                # Always close the client connection
                try:
                    client.close()
                except:
                    # Ignore errors during cleanup
                    pass
        
        return neo4j_query_tool
    
    def setup_agent(self) -> Agent:
        """Set up Agent with system prompt.
        
        Returns:
            Configured Agent instance
        """
        system_prompt = """
You are an assistant that can query a Neo4j database.

Rules:
- Call the tool `neo4j_query_tool` if data is required.
- Output ONLY the tool call.
- Do NOT include any other text, thoughts, explanations, or commentary
  in the same message as a tool call.
- After the tool result is returned, you may explain the answer.

Safety:
- Only generate READ-ONLY Cypher.
- Never use CREATE, MERGE, DELETE, SET, DROP, CALL, or APOC.
        """
        
        agent = Agent(
            model=self.bedrock_model,
            tools=[self.neo4j_tool],
            system_prompt=system_prompt.strip()
        )
        
        return agent
    
    def query(self, question: str) -> str:
        """Process a query through the Strands agent.
        
        Args:
            question: User question/query
            
        Returns:
            Agent response as string
            
        Raises:
            ValueError: If agent is not initialized or query is invalid
        """
        logger = logging.getLogger(__name__)
        
        if not self.agent:
            logger.error("Agent not initialized when attempting to process query")
            raise ValueError("Agent not initialized")
        
        # Validate the input query
        try:
            validated_question = validate_query_input(question)
            logger.info(f"Processing query: {validated_question[:100]}{'...' if len(validated_question) > 100 else ''}")
        except ValueError as e:
            logger.error(f"Query validation failed: {e}")
            raise e
        
        try:
            response = self.agent(validated_question)
            logger.info("Query processed successfully")
            logger.debug(f"Response length: {len(str(response))} characters")
            return response
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise ValueError(f"Query processing failed: {e}")
    
    def close(self) -> None:
        """Clean up resources."""
        # Note: Individual Neo4j clients are closed after each query
        # No persistent connections to clean up
        pass


class CLIInterface:
    """Command Line Interface for the Research Query Agent."""
    
    def __init__(self, agent: ResearchQueryAgent):
        """Initialize CLI interface with agent.
        
        Args:
            agent: ResearchQueryAgent instance
        """
        self.agent = agent
    
    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments.
        
        Returns:
            Parsed arguments namespace
        """
        parser = argparse.ArgumentParser(
            description='Research Query Agent - Query Neo4j database using natural language through AWS Bedrock',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s "Find authors with more than 10 publications"
  %(prog)s --interactive
  %(prog)s --help
            """.strip()
        )
        
        parser.add_argument(
            'query',
            nargs='?',
            help='Natural language query to execute against the Neo4j database'
        )
        
        parser.add_argument(
            '-i', '--interactive',
            action='store_true',
            help='Start interactive mode for multiple queries'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version='Research Query Agent 1.0.0'
        )
        
        return parser.parse_args()
    
    def run_single_query(self, query: str) -> None:
        """Execute a single query and display results.
        
        Args:
            query: User query string
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Validate the query input
            validated_query = validate_query_input(query)
            
            print(f"Executing query: {validated_query}")
            print("-" * 50)
            
            logger.info(f"Executing single query: {validated_query[:100]}{'...' if len(validated_query) > 100 else ''}")
            
            response = self.agent.query(validated_query)
            formatted_response = self.format_results(response)
            
            print(formatted_response)
            logger.info("Single query executed successfully")
            
        except ValueError as e:
            logger.error(f"Query validation error: {e}")
            self.handle_error(e)
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during single query execution: {e}")
            self.handle_error(e)
            sys.exit(1)
    
    def run_interactive_mode(self) -> None:
        """Run interactive mode for continuous queries."""
        logger = logging.getLogger(__name__)
        
        print("Research Query Agent - Interactive Mode")
        print("Type 'exit', 'quit', or press Ctrl+C to exit")
        print("-" * 50)
        
        logger.info("Starting interactive mode")
        
        try:
            while True:
                try:
                    query = input("\nEnter your query: ").strip()
                    
                    if not query:
                        continue
                    
                    if query.lower() in ['exit', 'quit', 'q']:
                        print("Goodbye!")
                        logger.info("Interactive mode exited by user command")
                        break
                    
                    # Validate the query input
                    try:
                        validated_query = validate_query_input(query)
                        logger.debug(f"Interactive query validated: {validated_query[:50]}{'...' if len(validated_query) > 50 else ''}")
                    except ValueError as e:
                        logger.warning(f"Invalid query in interactive mode: {e}")
                        print(f"Invalid query: {e}")
                        continue
                    
                    print(f"Executing: {validated_query}")
                    print("-" * 30)
                    
                    response = self.agent.query(validated_query)
                    formatted_response = self.format_results(response)
                    
                    print(formatted_response)
                    logger.debug("Interactive query processed successfully")
                    
                except KeyboardInterrupt:
                    print("\n\nGoodbye!")
                    logger.info("Interactive mode interrupted by user (Ctrl+C)")
                    break
                except Exception as e:
                    logger.error(f"Error during interactive query processing: {e}")
                    self.handle_error(e)
                    # Continue in interactive mode even after errors
                    continue
                    
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            logger.info("Interactive mode interrupted by user (Ctrl+C)")
    
    def format_results(self, response) -> str:
        """Format query results for display.
        
        Args:
            response: Raw response from agent (could be AgentResult or string)
            
        Returns:
            Formatted response string
        """
        logger = logging.getLogger(__name__)
        
        # Handle None or empty responses
        if not response:
            logger.debug("Empty response received, returning 'No results' message")
            return "No results returned."
        
        # Extract content from different response types
        formatted_content = self._extract_response_content(response)
        
        if not formatted_content or formatted_content.strip() == "":
            logger.debug("Response content is empty after extraction")
            return "No results returned."
        
        # Apply formatting based on content type
        formatted_response = self._apply_content_formatting(formatted_content)
        
        # Add separator line for visual clarity
        formatted_response += "\n" + "-" * 50
        
        logger.debug(f"Formatted response length: {len(formatted_response)} characters")
        return formatted_response
    
    def _extract_response_content(self, response) -> str:
        """Extract content from various response types.
        
        Args:
            response: Raw response from agent
            
        Returns:
            Extracted content as string
        """
        # Handle AgentResult objects (Strands framework response type)
        if hasattr(response, 'content'):
            return str(response.content).strip()
        
        # Handle objects with custom string representation
        elif hasattr(response, '__str__'):
            return str(response).strip()
        
        # Fallback to string conversion
        else:
            return str(response).strip()
    
    def _apply_content_formatting(self, content: str) -> str:
        """Apply formatting to improve readability of content.
        
        Args:
            content: Raw content string
            
        Returns:
            Formatted content string
        """
        # Check if content indicates empty results first (higher priority)
        if self._is_empty_result_content(content):
            return self._format_empty_result_content(content)
        
        # Check if content contains error information
        elif self._is_error_content(content):
            return self._format_error_content(content)
        
        # Check if content looks like structured data (JSON-like or contains specific patterns)
        elif self._is_structured_data(content):
            return self._format_structured_data(content)
        
        # Apply general text formatting
        else:
            return self._format_general_text(content)
    
    def _is_structured_data(self, content: str) -> bool:
        """Check if content appears to be structured data."""
        # Look for patterns that suggest structured data
        structured_indicators = [
            'row_count',
            'records',
            '"title"',
            '"name"',
            'MATCH (',
            'RETURN ',
            '{"',
            '[{',
        ]
        
        return any(indicator in content for indicator in structured_indicators)
    
    def _is_error_content(self, content: str) -> bool:
        """Check if content contains error information."""
        error_indicators = [
            'error',
            'Error',
            'ERROR',
            'failed',
            'Failed',
            'exception',
            'Exception',
            'cypher_validation_error',
            'database_connection_error',
            'query_execution_error'
        ]
        
        return any(indicator in content for indicator in error_indicators)
    
    def _is_empty_result_content(self, content: str) -> bool:
        """Check if content indicates empty results."""
        content_lower = content.lower()
        empty_indicators = [
            'no results',
            'no data',
            'empty result',
            'row_count": 0',
            'records": []',
            'no works',
            'no authors',
            'no data found',
            'query returned no',
            'returned 0 rows',
            'no matches found',
            'no entries found'
        ]
        
        return any(indicator in content_lower for indicator in empty_indicators)
    
    def _format_structured_data(self, content: str) -> str:
        """Format structured data for better readability."""
        # Add header for structured data
        formatted = "Query Results:\n"
        formatted += "=" * 40 + "\n\n"
        
        # Try to extract and format key information
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                # Add indentation for better structure
                if line.startswith(('MATCH', 'RETURN', 'WHERE', 'ORDER BY', 'LIMIT')):
                    formatted += f"Query: {line}\n"
                elif 'row_count' in line.lower():
                    formatted += f"Results: {line}\n"
                elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                    formatted += f"  {line}\n"
                else:
                    formatted += f"{line}\n"
        
        return formatted
    
    def _format_error_content(self, content: str) -> str:
        """Format error content with clear error indication."""
        formatted = "Error Occurred:\n"
        formatted += "=" * 40 + "\n\n"
        formatted += f"❌ {content}\n"
        return formatted
    
    def _format_empty_result_content(self, content: str) -> str:
        """Format empty result content with helpful message."""
        formatted = "Query Completed:\n"
        formatted += "=" * 40 + "\n\n"
        formatted += f"ℹ️  {content}\n\n"
        formatted += "Suggestions:\n"
        formatted += "- Try a different search term\n"
        formatted += "- Check if the data exists in the database\n"
        formatted += "- Verify your query syntax\n"
        return formatted
    
    def _format_general_text(self, content: str) -> str:
        """Format general text content for better readability."""
        # Add header for general results
        formatted = "Response:\n"
        formatted += "=" * 40 + "\n\n"
        
        # Split into paragraphs and format
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Add some spacing for readability
                formatted += f"{paragraph}\n\n"
        
        return formatted.rstrip() + "\n"
    
    def handle_error(self, error: Exception) -> None:
        """Handle and display errors in a user-friendly way.
        
        Args:
            error: Exception that occurred
        """
        error_message = str(error)
        
        print(f"Error: {error_message}", file=sys.stderr)
        
        # Provide helpful hints for common errors
        if "Failed to initialize Bedrock model" in error_message:
            print("\nTroubleshooting tips:", file=sys.stderr)
            print("- Check your AWS credentials in the .env file", file=sys.stderr)
            print("- Ensure your AWS region supports Bedrock service", file=sys.stderr)
            print("- Verify your AWS account has Bedrock permissions", file=sys.stderr)
        elif "Missing required environment variables" in error_message:
            print("\nTroubleshooting tips:", file=sys.stderr)
            print("- Create a .env file with required variables", file=sys.stderr)
            print("- Check that all environment variables are properly set", file=sys.stderr)
        elif "cypher_validation_error" in error_message:
            print("\nTroubleshooting tips:", file=sys.stderr)
            print("- Try rephrasing your query", file=sys.stderr)
            print("- Ensure you're asking for read-only operations", file=sys.stderr)
        elif "query_execution_error" in error_message:
            print("\nTroubleshooting tips:", file=sys.stderr)
            print("- Check your Neo4j database connection", file=sys.stderr)
            print("- Verify the database is running and accessible", file=sys.stderr)


def main():
    """Main entry point for the script."""
    # Set up logging first
    setup_logging(level=os.getenv('LOG_LEVEL', 'INFO'))
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Research Query Agent")
        
        # Initialize configuration and agent
        logger.debug("Initializing configuration manager")
        config_manager = ConfigManager()
        
        logger.debug("Initializing research query agent")
        agent = ResearchQueryAgent(config_manager)
        
        logger.debug("Initializing CLI interface")
        cli = CLIInterface(agent)
        
        # Parse command line arguments
        logger.debug("Parsing command line arguments")
        args = cli.parse_arguments()
        
        # Validate arguments
        try:
            validate_cli_arguments(args)
        except ValueError as e:
            logger.error(f"Invalid command line arguments: {e}")
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)  # Exit code 2 for invalid arguments
        
        # Determine execution mode
        if args.interactive:
            logger.info("Starting interactive mode")
            cli.run_interactive_mode()
        elif args.query:
            logger.info("Starting single query mode")
            cli.run_single_query(args.query)
        else:
            logger.info("No query provided, starting interactive mode by default")
            cli.run_interactive_mode()
        
        logger.info("Research Query Agent completed successfully")
        sys.exit(0)  # Exit code 0 for success
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user (Ctrl+C)")
        print("\n\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except ValueError as e:
        logger.error(f"Configuration or validation error: {e}")
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(3)  # Exit code 3 for configuration errors
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)  # Exit code 1 for general errors
    finally:
        # Clean up resources
        try:
            if 'agent' in locals():
                logger.debug("Cleaning up agent resources")
                agent.close()
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {cleanup_error}")
            # Don't fail the program due to cleanup errors


if __name__ == "__main__":
    main()