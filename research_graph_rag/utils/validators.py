"""
Cypher query validation utilities.

Provides validation for Cypher queries to ensure they are safe and read-only.
"""

import re
from typing import List, Set
from .exceptions import ValidationError


class CypherValidator:
    """Validates Cypher queries for safety and correctness."""
    
    # Forbidden keywords that indicate write operations
    FORBIDDEN_KEYWORDS = {
        'CREATE', 'MERGE', 'DELETE', 'REMOVE', 'SET', 'DROP', 
        'DETACH DELETE', 'FOREACH', 'LOAD CSV'
    }
    
    # Allowed procedure prefixes
    ALLOWED_PROCEDURES = {
        'gds.',  # Graph Data Science
        'db.labels',
        'db.relationshipTypes', 
        'db.propertyKeys',
        'db.schema',
        'dbms.components'
    }
    
    # Valid node labels
    VALID_LABELS = {'Author', 'Work', 'Topic'}
    
    # Valid relationship types
    VALID_RELATIONSHIPS = {
        'WORK_AUTHORED_BY', 'WORK_HAS_TOPIC', 'RELATED_TO',
        'COLLABORATED_WITH', 'SHARES_TOPIC_WITH'
    }
    
    @classmethod
    def assert_read_only(cls, cypher: str) -> None:
        """Assert that a Cypher query is read-only.
        
        Args:
            cypher: Cypher query string
            
        Raises:
            ValidationError: If query contains write operations
        """
        cypher_upper = cypher.upper()
        
        # Check for forbidden keywords
        for keyword in cls.FORBIDDEN_KEYWORDS:
            if keyword in cypher_upper:
                raise ValidationError(
                    f"Write operation not allowed: {keyword}",
                    validation_type="read_only_check",
                    invalid_value=keyword
                )
        
        # Check for CALL procedures (allow only specific ones)
        if 'CALL ' in cypher_upper:
            cls._validate_procedure_calls(cypher)
    
    @classmethod
    def _validate_procedure_calls(cls, cypher: str) -> None:
        """Validate CALL procedure statements."""
        # Find all CALL statements
        call_pattern = r'CALL\s+([a-zA-Z0-9_.]+)'
        calls = re.findall(call_pattern, cypher, re.IGNORECASE)
        
        for call in calls:
            call_lower = call.lower()
            
            # Check if it's an allowed procedure
            allowed = any(call_lower.startswith(prefix) for prefix in cls.ALLOWED_PROCEDURES)
            
            if not allowed:
                raise ValidationError(
                    f"Procedure call not allowed: {call}",
                    validation_type="procedure_validation",
                    invalid_value=call
                )
    
    @classmethod
    def validate_labels(cls, cypher: str) -> None:
        """Validate node labels in the query.
        
        Args:
            cypher: Cypher query string
            
        Raises:
            ValidationError: If query contains invalid labels
        """
        # Find all node labels (pattern: :LabelName)
        label_pattern = r':([A-Za-z][A-Za-z0-9_]*)'
        labels = re.findall(label_pattern, cypher)
        
        for label in labels:
            if label not in cls.VALID_LABELS:
                raise ValidationError(
                    f"Invalid node label: {label}. Valid labels: {', '.join(cls.VALID_LABELS)}",
                    validation_type="label_validation",
                    invalid_value=label
                )
    
    @classmethod
    def validate_relationships(cls, cypher: str) -> None:
        """Validate relationship types in the query.
        
        Args:
            cypher: Cypher query string
            
        Raises:
            ValidationError: If query contains invalid relationships
        """
        # Find all relationship types (pattern: [:RELATIONSHIP_TYPE])
        rel_pattern = r'\[:([A-Za-z_][A-Za-z0-9_]*)\]'
        relationships = re.findall(rel_pattern, cypher)
        
        for rel in relationships:
            if rel not in cls.VALID_RELATIONSHIPS:
                raise ValidationError(
                    f"Invalid relationship type: {rel}. Valid types: {', '.join(cls.VALID_RELATIONSHIPS)}",
                    validation_type="relationship_validation", 
                    invalid_value=rel
                )
    
    @classmethod
    def validate_properties(cls, cypher: str) -> None:
        """Validate property access patterns.
        
        Args:
            cypher: Cypher query string
            
        Raises:
            ValidationError: If query contains suspicious property access
        """
        # Check for potential injection patterns
        suspicious_patterns = [
            r'["\'].*["\'].*\+.*["\']',  # String concatenation
            r'["\'].*\$.*["\']',         # Parameter injection
            r'["\'].*\{.*\}.*["\']',     # Template injection
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, cypher, re.IGNORECASE):
                raise ValidationError(
                    "Suspicious property access pattern detected",
                    validation_type="property_validation",
                    invalid_value=pattern
                )
    
    @classmethod
    def prepare_cypher(cls, cypher: str) -> str:
        """Prepare and clean a Cypher query.
        
        Args:
            cypher: Raw Cypher query string
            
        Returns:
            Cleaned and prepared Cypher query
            
        Raises:
            ValidationError: If query is invalid
        """
        if not cypher or not cypher.strip():
            raise ValidationError("Cypher query cannot be empty")
        
        # Clean the query
        cleaned = cypher.strip()
        
        # Remove comments
        cleaned = re.sub(r'//.*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Basic validation
        cls.assert_read_only(cleaned)
        
        return cleaned
    
    @classmethod
    def validate_query_structure(cls, cypher: str) -> None:
        """Validate the overall structure of a Cypher query.
        
        Args:
            cypher: Cypher query string
            
        Raises:
            ValidationError: If query structure is invalid
        """
        cypher_upper = cypher.upper()
        
        # Check for balanced parentheses
        if cypher.count('(') != cypher.count(')'):
            raise ValidationError(
                "Unbalanced parentheses in query",
                validation_type="structure_validation"
            )
        
        # Check for balanced brackets
        if cypher.count('[') != cypher.count(']'):
            raise ValidationError(
                "Unbalanced brackets in query", 
                validation_type="structure_validation"
            )
        
        # Check for balanced braces
        if cypher.count('{') != cypher.count('}'):
            raise ValidationError(
                "Unbalanced braces in query",
                validation_type="structure_validation"
            )
        
        # Ensure query has a RETURN or YIELD clause (unless it's a CALL)
        if not any(keyword in cypher_upper for keyword in ['RETURN', 'YIELD']) and 'CALL' not in cypher_upper:
            raise ValidationError(
                "Query must have a RETURN or YIELD clause",
                validation_type="structure_validation"
            )
    
    @classmethod
    def validate_full(cls, cypher: str) -> str:
        """Perform full validation on a Cypher query.
        
        Args:
            cypher: Cypher query string
            
        Returns:
            Validated and prepared query
            
        Raises:
            ValidationError: If any validation fails
        """
        # Prepare the query
        prepared = cls.prepare_cypher(cypher)
        
        # Run all validations
        cls.validate_query_structure(prepared)
        cls.validate_properties(prepared)
        
        # Skip label/relationship validation for GDS queries
        if 'CALL gds.' not in prepared.upper():
            cls.validate_labels(prepared)
            cls.validate_relationships(prepared)
        
        return prepared


class EnhancedCypherValidator(CypherValidator):
    """Enhanced Cypher validator with support for relationship inference patterns."""
    
    # Additional valid relationships for inference
    ENHANCED_RELATIONSHIPS = CypherValidator.VALID_RELATIONSHIPS | {
        'CO_AUTHORED', 'WORKS_WITH', 'SIMILAR_TO'
    }
    
    @classmethod
    def validate_enhanced_relationships(cls, cypher: str) -> None:
        """Validate relationships including inferred ones."""
        # Find all relationship types
        rel_pattern = r'\[:([A-Za-z_][A-Za-z0-9_]*)\]'
        relationships = re.findall(rel_pattern, cypher)
        
        for rel in relationships:
            if rel not in cls.ENHANCED_RELATIONSHIPS:
                # Allow some common inference patterns
                inference_patterns = [
                    "COLLABORATED_WITH", "SHARES_TOPIC_WITH", 
                    "CO_AUTHORED", "WORKS_WITH"
                ]
                
                if rel not in inference_patterns:
                    raise ValidationError(
                        f"Unknown relationship: {rel}",
                        validation_type="enhanced_relationship_validation",
                        invalid_value=rel
                    )
    
    @classmethod
    def enhance_query_for_relationships(cls, cypher: str) -> str:
        """Enhance queries to better support relationship inference."""
        # Replace common relationship aliases with patterns
        enhancements = {
            # Co-authorship patterns
            r"COLLABORATED_WITH": "[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]",
            r"CO_AUTHORED": "[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]",
            
            # Topic sharing patterns  
            r"SHARES_TOPIC_WITH": "[:WORK_AUTHORED_BY]->(:Work)-[:WORK_HAS_TOPIC]->(:Topic)<-[:WORK_HAS_TOPIC]-(:Work)<-[:WORK_AUTHORED_BY]",
        }
        
        enhanced_cypher = cypher
        for pattern, replacement in enhancements.items():
            enhanced_cypher = re.sub(f"-\\[:{pattern}\\]->", f"-{replacement}-", enhanced_cypher)
        
        return enhanced_cypher