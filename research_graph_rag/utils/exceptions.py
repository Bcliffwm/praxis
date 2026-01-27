"""
Custom exceptions for Research GraphRAG package.

Provides specific exception types for different error conditions.
"""


class GraphRAGError(Exception):
    """Base exception for Research GraphRAG package."""
    
    def __init__(self, message: str, details: dict = None):
        """Initialize GraphRAG error.
        
        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(GraphRAGError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_field: str = None):
        """Initialize configuration error.
        
        Args:
            message: Error message
            config_field: Optional field name that caused the error
        """
        details = {"config_field": config_field} if config_field else {}
        super().__init__(message, details)
        self.config_field = config_field


class ValidationError(GraphRAGError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, validation_type: str = None, invalid_value: str = None):
        """Initialize validation error.
        
        Args:
            message: Error message
            validation_type: Type of validation that failed
            invalid_value: The value that failed validation
        """
        details = {}
        if validation_type:
            details["validation_type"] = validation_type
        if invalid_value:
            details["invalid_value"] = invalid_value
        
        super().__init__(message, details)
        self.validation_type = validation_type
        self.invalid_value = invalid_value


class DatabaseError(GraphRAGError):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, query: str = None, database: str = None):
        """Initialize database error.
        
        Args:
            message: Error message
            query: Optional Cypher query that caused the error
            database: Optional database name
        """
        details = {}
        if query:
            details["query"] = query
        if database:
            details["database"] = database
        
        super().__init__(message, details)
        self.query = query
        self.database = database


class NetworkAnalysisError(GraphRAGError):
    """Exception raised for network analysis errors."""
    
    def __init__(self, message: str, analysis_type: str = None, graph_name: str = None):
        """Initialize network analysis error.
        
        Args:
            message: Error message
            analysis_type: Type of analysis that failed
            graph_name: Name of the graph projection
        """
        details = {}
        if analysis_type:
            details["analysis_type"] = analysis_type
        if graph_name:
            details["graph_name"] = graph_name
        
        super().__init__(message, details)
        self.analysis_type = analysis_type
        self.graph_name = graph_name