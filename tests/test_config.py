"""
Tests for configuration management.
"""

import pytest
import os
from unittest.mock import patch, mock_open
from research_graph_rag.core.config import ConfigManager, Config
from research_graph_rag.utils.exceptions import ConfigurationError


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    def test_config_initialization(self):
        """Test basic config initialization."""
        with patch.dict(os.environ, {
            'DB_URI': 'bolt://localhost:7687',
            'DB_USER': 'neo4j',
            'DB_PASSWORD': 'password',
            'TARGET_DB': 'praxis',
            'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
            'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'region_name': 'us-east-1'
        }):
            config_manager = ConfigManager()
            assert config_manager.config is not None
            assert config_manager.config.db_uri == 'bolt://localhost:7687'
            assert config_manager.config.db_user == 'neo4j'
    
    def test_missing_required_fields(self):
        """Test error handling for missing required fields."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigManager()
            assert "Missing required environment variables" in str(exc_info.value)
    
    def test_invalid_neo4j_uri(self):
        """Test validation of Neo4j URI format."""
        with patch.dict(os.environ, {
            'DB_URI': 'invalid://localhost:7687',
            'DB_USER': 'neo4j',
            'DB_PASSWORD': 'password',
            'TARGET_DB': 'praxis',
            'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
            'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'region_name': 'us-east-1'
        }):
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigManager()
            assert "Invalid Neo4j URI format" in str(exc_info.value)
    
    def test_get_neo4j_config(self):
        """Test Neo4j configuration extraction."""
        with patch.dict(os.environ, {
            'DB_URI': 'bolt://localhost:7687',
            'DB_USER': 'neo4j',
            'DB_PASSWORD': 'password',
            'TARGET_DB': 'praxis',
            'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
            'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'region_name': 'us-east-1'
        }):
            config_manager = ConfigManager()
            neo4j_config = config_manager.get_neo4j_config()
            
            assert neo4j_config['uri'] == 'bolt://localhost:7687'
            assert neo4j_config['auth'] == ('neo4j', 'password')
            assert neo4j_config['database'] == 'praxis'
    
    def test_get_aws_config(self):
        """Test AWS configuration extraction."""
        with patch.dict(os.environ, {
            'DB_URI': 'bolt://localhost:7687',
            'DB_USER': 'neo4j',
            'DB_PASSWORD': 'password',
            'TARGET_DB': 'praxis',
            'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
            'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'region_name': 'us-east-1'
        }):
            config_manager = ConfigManager()
            aws_config = config_manager.get_aws_config()
            
            assert aws_config['aws_access_key_id'] == 'AKIAIOSFODNN7EXAMPLE'
            assert aws_config['aws_secret_access_key'] == 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
            assert aws_config['region_name'] == 'us-east-1'
    
    def test_to_dict_excludes_sensitive_data(self):
        """Test that to_dict excludes sensitive information."""
        with patch.dict(os.environ, {
            'DB_URI': 'bolt://localhost:7687',
            'DB_USER': 'neo4j',
            'DB_PASSWORD': 'password',
            'TARGET_DB': 'praxis',
            'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
            'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            'region_name': 'us-east-1'
        }):
            config_manager = ConfigManager()
            config_dict = config_manager.to_dict()
            
            # Should include non-sensitive data
            assert 'db_uri' in config_dict
            assert 'db_user' in config_dict
            assert 'region_name' in config_dict
            
            # Should exclude sensitive data
            assert 'db_password' not in config_dict
            assert 'aws_secret_access_key' not in config_dict
            
            # Should include flags for sensitive data
            assert 'aws_credentials_configured' in config_dict
            assert 'db_password_configured' in config_dict