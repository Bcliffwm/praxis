"""
Configuration management for Research GraphRAG package.

Handles environment variable loading, validation, and configuration
for Neo4j database connections and AWS Bedrock integration.
"""

import os
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from ..utils.exceptions import ConfigurationError


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
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize ConfigManager and load configuration.
        
        Args:
            env_file: Optional path to .env file. If None, uses default .env
        """
        self.config: Optional[Config] = None
        self.env_file = env_file
        self.load_environment()
        self.validate_config()
    
    def load_environment(self) -> None:
        """Load environment variables from .env file."""
        # Try to load .env file
        env_file_loaded = load_dotenv(self.env_file) if self.env_file else load_dotenv()
        
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
            raise ConfigurationError(error_message)
    
    def validate_config(self) -> None:
        """Validate that all required configuration values are present and properly formatted."""
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        
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
            
            raise ConfigurationError(error_message)
    
    def _validate_field_format(self, field_name: str, value: str, env_var_name: str) -> Optional[str]:
        """Validate the format of specific configuration fields."""
        if field_name == 'db_uri':
            # Validate Neo4j URI format
            if not (value.startswith('bolt://') or value.startswith('neo4j://') or 
                   value.startswith('bolt+s://') or value.startswith('neo4j+s://')):
                return f"Invalid Neo4j URI format for {env_var_name}: '{value}'. Expected format: bolt://host:port or neo4j://host:port"
        
        elif field_name == 'aws_access_key_id':
            # Validate AWS Access Key ID format
            if not (value.startswith(('AKIA', 'ASIA')) and len(value) == 20):
                return f"Invalid AWS Access Key ID format for {env_var_name}: '{value}'. Expected format: 20-character string starting with AKIA or ASIA"
        
        elif field_name == 'aws_secret_access_key':
            # Validate AWS Secret Access Key format
            if len(value) != 40:
                return f"Invalid AWS Secret Access Key format for {env_var_name}: Secret key should be 40 characters long"
        
        elif field_name == 'region_name':
            # Validate AWS region format
            if not re.match(r'^[a-z]{2}-[a-z]+-\d+$', value):
                return f"Invalid AWS region format for {env_var_name}: '{value}'. Expected format: us-east-1, eu-west-1, etc."
        
        elif field_name in ['db_user', 'db_password', 'target_db']:
            # Basic validation for database fields
            if not value.strip():
                return f"Invalid value for {env_var_name}: Cannot be empty or whitespace only"
        
        return None
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j connection configuration."""
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        
        return {
            'uri': self.config.db_uri,
            'auth': (self.config.db_user, self.config.db_password),
            'database': self.config.target_db
        }
    
    def get_aws_config(self) -> Dict[str, Any]:
        """Get AWS connection configuration."""
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        
        return {
            'aws_access_key_id': self.config.aws_access_key_id,
            'aws_secret_access_key': self.config.aws_secret_access_key,
            'region_name': self.config.region_name
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        if not self.config:
            return {}
        
        return {
            'db_uri': self.config.db_uri,
            'db_user': self.config.db_user,
            'target_db': self.config.target_db,
            'region_name': self.config.region_name,
            # Exclude sensitive fields
            'aws_credentials_configured': bool(self.config.aws_access_key_id),
            'db_password_configured': bool(self.config.db_password)
        }