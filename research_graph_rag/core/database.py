"""
Database client for Neo4j connections.

Provides a robust Neo4j client with connection management,
error handling, and query execution capabilities.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from neo4j import GraphDatabase

from ..utils.exceptions import GraphRAGError

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j database client with connection management."""
    
    def __init__(self, uri: str, auth: Tuple[str, str], database: str):
        """Initialize Neo4j client with connection parameters.
        
        Args:
            uri: Neo4j database URI
            auth: Authentication tuple (username, password)
            database: Target database name
            
        Raises:
            GraphRAGError: If connection parameters are invalid or connection fails
        """
        self.database = database
        self.uri = uri
        self.auth = auth
        
        try:
            self.driver = GraphDatabase.driver(uri=uri, auth=auth)
            self._test_connection()
            logger.info(f"Successfully connected to Neo4j database: {database}")
            
        except Exception as e:
            error_message = self._format_connection_error(e, uri, auth[0])
            logger.error(f"Neo4j connection failed: {error_message}")
            raise GraphRAGError(error_message)
    
    def _test_connection(self) -> None:
        """Test the database connection to ensure it's working."""
        try:
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1 AS test")
            logger.debug("Neo4j connection test successful")
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            raise e
    
    def _format_connection_error(self, error: Exception, uri: str, username: str) -> str:
        """Format connection errors with helpful messages."""
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
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.close()
                logger.debug("Neo4j connection closed")
            except Exception as e:
                logger.warning(f"Error closing Neo4j connection: {e}")
    
    def run_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            params: Optional query parameters
            
        Returns:
            List of dictionaries containing query results
            
        Raises:
            GraphRAGError: If query execution fails
        """
        try:
            with self.driver.session(database=self.database) as session:
                logger.debug(f"Executing Cypher query: {query[:100]}...")
                result = session.run(query, params or {})
                records = [record.data() for record in result]
                logger.debug(f"Query returned {len(records)} records")
                return records
        except Exception as e:
            error_message = self._format_query_error(e, query)
            logger.error(f"Cypher query execution failed: {error_message}")
            raise GraphRAGError(error_message)
    
    def _format_query_error(self, error: Exception, query: str) -> str:
        """Format query execution errors with helpful messages."""
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
    
    def test_gds_availability(self) -> bool:
        """Test if Neo4j Graph Data Science library is available."""
        try:
            query = "CALL gds.version() YIELD gdsVersion RETURN gdsVersion"
            result = self.run_cypher(query)
            if result:
                gds_version = result[0].get('gdsVersion', 'Unknown')
                logger.info(f"Neo4j GDS available, version: {gds_version}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Neo4j GDS not available: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get basic database information."""
        try:
            # Get node counts
            node_query = """
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
            """
            node_results = self.run_cypher(node_query)
            
            # Get relationship counts
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """
            rel_results = self.run_cypher(rel_query)
            
            return {
                'database': self.database,
                'uri': self.uri,
                'nodes': node_results,
                'relationships': rel_results,
                'gds_available': self.test_gds_availability()
            }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {
                'database': self.database,
                'uri': self.uri,
                'error': str(e)
            }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()