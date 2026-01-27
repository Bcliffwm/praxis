"""
Tests for Cypher query validators.
"""

import pytest
from research_graph_rag.utils.validators import CypherValidator, EnhancedCypherValidator
from research_graph_rag.utils.exceptions import ValidationError


class TestCypherValidator:
    """Test cases for CypherValidator."""
    
    def test_valid_read_only_query(self):
        """Test validation of valid read-only queries."""
        valid_queries = [
            "MATCH (n:Author) RETURN n.name",
            "MATCH (w:Work)-[:WORK_HAS_TOPIC]->(t:Topic) RETURN w.title, t.display_name",
            "MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work) WHERE a.name = 'John Doe' RETURN w.title"
        ]
        
        for query in valid_queries:
            # Should not raise an exception
            CypherValidator.assert_read_only(query)
    
    def test_forbidden_write_operations(self):
        """Test detection of forbidden write operations."""
        forbidden_queries = [
            "CREATE (n:Author {name: 'Test'})",
            "MERGE (w:Work {title: 'Test Work'})",
            "DELETE n",
            "SET n.name = 'Updated'",
            "DROP INDEX ON :Author(name)"
        ]
        
        for query in forbidden_queries:
            with pytest.raises(ValidationError) as exc_info:
                CypherValidator.assert_read_only(query)
            assert "Write operation not allowed" in str(exc_info.value)
    
    def test_valid_labels(self):
        """Test validation of valid node labels."""
        valid_query = "MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work)-[:WORK_HAS_TOPIC]->(t:Topic) RETURN a, w, t"
        # Should not raise an exception
        CypherValidator.validate_labels(valid_query)
    
    def test_invalid_labels(self):
        """Test detection of invalid node labels."""
        invalid_query = "MATCH (x:InvalidLabel) RETURN x"
        with pytest.raises(ValidationError) as exc_info:
            CypherValidator.validate_labels(invalid_query)
        assert "Invalid node label: InvalidLabel" in str(exc_info.value)
    
    def test_valid_relationships(self):
        """Test validation of valid relationship types."""
        valid_query = "MATCH (a:Author)-[:WORK_AUTHORED_BY]->(w:Work)-[:WORK_HAS_TOPIC]->(t:Topic) RETURN a, w, t"
        # Should not raise an exception
        CypherValidator.validate_relationships(valid_query)
    
    def test_invalid_relationships(self):
        """Test detection of invalid relationship types."""
        invalid_query = "MATCH (a:Author)-[:INVALID_RELATIONSHIP]->(w:Work) RETURN a, w"
        with pytest.raises(ValidationError) as exc_info:
            CypherValidator.validate_relationships(invalid_query)
        assert "Invalid relationship type: INVALID_RELATIONSHIP" in str(exc_info.value)
    
    def test_prepare_cypher_cleans_query(self):
        """Test that prepare_cypher cleans and normalizes queries."""
        messy_query = """
        // This is a comment
        MATCH    (n:Author)   
        /* Multi-line
           comment */
        RETURN     n.name    
        """
        
        cleaned = CypherValidator.prepare_cypher(messy_query)
        
        # Should remove comments and normalize whitespace
        assert "//" not in cleaned
        assert "/*" not in cleaned
        assert "*/" not in cleaned
        assert "MATCH (n:Author) RETURN n.name" in cleaned
    
    def test_empty_query_validation(self):
        """Test validation of empty queries."""
        with pytest.raises(ValidationError) as exc_info:
            CypherValidator.prepare_cypher("")
        assert "Cypher query cannot be empty" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            CypherValidator.prepare_cypher("   ")
        assert "Cypher query cannot be empty" in str(exc_info.value)
    
    def test_query_structure_validation(self):
        """Test validation of query structure."""
        # Unbalanced parentheses
        with pytest.raises(ValidationError) as exc_info:
            CypherValidator.validate_query_structure("MATCH (n:Author RETURN n")
        assert "Unbalanced parentheses" in str(exc_info.value)
        
        # Unbalanced brackets
        with pytest.raises(ValidationError) as exc_info:
            CypherValidator.validate_query_structure("MATCH (n)-[r:RELATIONSHIP->(m) RETURN n")
        assert "Unbalanced brackets" in str(exc_info.value)
        
        # Missing RETURN clause
        with pytest.raises(ValidationError) as exc_info:
            CypherValidator.validate_query_structure("MATCH (n:Author)")
        assert "Query must have a RETURN or YIELD clause" in str(exc_info.value)
    
    def test_allowed_gds_procedures(self):
        """Test that GDS procedures are allowed."""
        gds_queries = [
            "CALL gds.pageRank.stream('graph') YIELD nodeId, score",
            "CALL gds.louvain.stream('graph') YIELD nodeId, communityId",
            "CALL gds.graph.project('graph', ['Author'], ['WORK_AUTHORED_BY'])"
        ]
        
        for query in gds_queries:
            # Should not raise an exception
            CypherValidator.assert_read_only(query)
    
    def test_forbidden_procedures(self):
        """Test that non-GDS procedures are forbidden."""
        forbidden_procedures = [
            "CALL apoc.create.node(['Author'], {name: 'Test'})",
            "CALL dbms.security.createUser('test', 'password')"
        ]
        
        for query in forbidden_procedures:
            with pytest.raises(ValidationError) as exc_info:
                CypherValidator.assert_read_only(query)
            assert "Procedure call not allowed" in str(exc_info.value)


class TestEnhancedCypherValidator:
    """Test cases for EnhancedCypherValidator."""
    
    def test_enhanced_relationships(self):
        """Test validation of enhanced relationship types."""
        enhanced_query = "MATCH (a1:Author)-[:COLLABORATED_WITH]->(a2:Author) RETURN a1, a2"
        # Should not raise an exception
        EnhancedCypherValidator.validate_enhanced_relationships(enhanced_query)
    
    def test_relationship_enhancement(self):
        """Test query enhancement for relationship patterns."""
        original_query = "MATCH (a1:Author)-[:COLLABORATED_WITH]->(a2:Author) RETURN a1, a2"
        enhanced_query = EnhancedCypherValidator.enhance_query_for_relationships(original_query)
        
        # Should replace the relationship pattern
        assert "[:WORK_AUTHORED_BY]->(:Work)<-[:WORK_AUTHORED_BY]" in enhanced_query
    
    def test_topic_sharing_enhancement(self):
        """Test enhancement of topic sharing patterns."""
        original_query = "MATCH (a1:Author)-[:SHARES_TOPIC_WITH]->(a2:Author) RETURN a1, a2"
        enhanced_query = EnhancedCypherValidator.enhance_query_for_relationships(original_query)
        
        # Should replace with complex topic sharing pattern
        assert "[:WORK_HAS_TOPIC]" in enhanced_query
        assert "(:Topic)" in enhanced_query