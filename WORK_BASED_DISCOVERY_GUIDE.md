# Work-Based Relationship Discovery Guide

## Overview
This guide shows how to use work titles or award numbers as input to find related works using the enhanced research query agent. This enables powerful GraphRAG capabilities for research portfolio analysis.

## Quick Start

### 1. Basic Setup
```python
from work_based_relationship_agent import WorkBasedRelationshipAgent, ConfigManager

# Initialize the agent
config_manager = ConfigManager()
agent = WorkBasedRelationshipAgent(config_manager)
```

### 2. Find Works by Title Keyword
```python
# Find works containing specific keywords
response = agent.query("Find works with titles containing 'machine learning'")
print(response)
```

### 3. Find Related Works
```python
# Find works related through various relationship types
response = agent.query("Show me works related to 'Deep Learning in Healthcare' through shared authors")
print(response)
```

### 4. Find Works by Award Number
```python
# Find all works funded by the same grant
response = agent.query("Find all works funded by award number 'NSF-2024-001'")
print(response)
```

## Discovery Methods

### 1. Title-Based Discovery
**Use Case**: You have a work title or keywords and want to find similar works.

```python
# Exact title search
agent.query("Find the work titled 'Clinical Characteristics of Coronavirus Disease 2019'")

# Partial title search
agent.query("Find works containing 'Collaborative Research'")

# Keyword-based search
agent.query("Show me works about 'machine learning' or 'artificial intelligence'")
```

**What it finds**:
- Works with matching or similar titles
- Works containing specific keywords
- Variations of title phrases

### 2. Author-Based Relationship Discovery
**Use Case**: Find other works by the same research team.

```python
# Find works by same authors
agent.query("Find works by the same authors as 'Multi-Author Investigation Study'")

# Find collaborative works
agent.query("Show me other collaborations involving the authors of 'Research Study 20'")
```

**What it finds**:
- Works authored by the same researchers
- Collaborative patterns within research teams
- Research continuity across projects

### 3. Topic-Based Relationship Discovery
**Use Case**: Find works in the same research domain or with similar themes.

```python
# Find topically related works
agent.query("Find works that share research topics with 'Ethnobotany and Biodiversity Study'")

# Find thematically similar works
agent.query("Show me works in similar research areas to 'Environmental Policy Research'")
```

**What it finds**:
- Works sharing common research topics
- Thematically related research
- Cross-disciplinary connections

### 4. Award-Based Discovery
**Use Case**: Track research outputs from specific funding sources.

```python
# Find works by award number
agent.query("Find all works funded by grant 'NIH-R01-2024-12345'")

# Find related funding
agent.query("Show me research projects with the same funding source as 'Study ABC'")
```

**What it finds**:
- All works funded by the same grant
- Research portfolio of funding agencies
- Impact assessment of specific awards

### 5. Comprehensive Multi-Type Discovery
**Use Case**: Get a complete picture of all related research.

```python
# Comprehensive relationship discovery
agent.query("Find all works related to 'Climate Change Research' through any relationship type")

# Multi-faceted discovery
agent.query("Show me everything related to 'Biomedical Engineering Study' - authors, topics, and funding")
```

**What it finds**:
- Author-based relationships
- Topic-based relationships
- Award-based relationships
- Explicit relationships
- Combined relationship strength

## Advanced Usage Patterns

### 1. Research Portfolio Analysis
```python
# Analyze a researcher's portfolio
agent.query("Find all works and collaborations related to Dr. Smith's research on 'Neural Networks'")

# Institutional portfolio
agent.query("Show me all works from MIT related to 'Artificial Intelligence' research")
```

### 2. Literature Review Expansion
```python
# Expand literature review
agent.query("Find works related to 'Quantum Computing Applications' for comprehensive literature review")

# Find seminal works
agent.query("Show me highly collaborative works in 'Machine Learning' research")
```

### 3. Collaboration Discovery
```python
# Find potential collaborators
agent.query("Find researchers working on similar topics to 'Sustainable Energy Systems'")

# Identify research networks
agent.query("Show me the collaboration network around 'Climate Change Mitigation' research")
```

### 4. Grant Impact Assessment
```python
# Assess grant impact
agent.query("Find all research outputs from NSF grant 'DMS-2024-001' and their collaborations")

# Track funding effectiveness
agent.query("Show me the research network created by 'NIH Collaborative Grant Program'")
```

## Query Patterns and Examples

### Natural Language Queries
The agent understands various natural language patterns:

```python
# Direct title queries
"Find the work titled 'X'"
"Show me works containing 'keyword'"

# Relationship queries
"Find works related to 'X'"
"Show me works by the same authors as 'X'"
"Find works sharing topics with 'X'"

# Award queries
"Find works funded by 'award_number'"
"Show me research from grant 'X'"

# Comprehensive queries
"Find everything related to 'X'"
"Show me all connections to 'research_topic'"
```

### Programmatic Usage
For programmatic access, use the direct methods:

```python
# Direct method calls
result = agent.find_works_by_title("machine learning")
result = agent.find_related_works(title_keyword="neural networks")
result = agent.find_works_by_award("NSF-2024-001")
```

## Response Structure

### Typical Response Format
```python
{
    "row_count": 15,
    "records": [
        {
            "work_id": "W123456",
            "title": "Machine Learning in Healthcare",
            "authors": ["Dr. Smith", "Dr. Jones"],
            "relationship_type": "shared_authors"
        }
        # ... more records
    ],
    "enhanced_analysis": {
        "total_works": 15,
        "query_type": "author_based_discovery",
        "insights": [
            "Found connections through 8 different authors",
            "Results include relationship strength indicators"
        ]
    }
}
```

### Key Fields
- **row_count**: Number of related works found
- **records**: Detailed information about each related work
- **enhanced_analysis**: AI-generated insights about the relationships
- **relationship_type**: How the works are connected (shared_authors, shared_topics, etc.)

## Integration Examples

### 1. Web Application Integration
```python
from flask import Flask, request, jsonify
from work_based_relationship_agent import WorkBasedRelationshipAgent, ConfigManager

app = Flask(__name__)
agent = WorkBasedRelationshipAgent(ConfigManager())

@app.route('/find_related_works', methods=['POST'])
def find_related_works():
    data = request.json
    title_keyword = data.get('title_keyword')
    award_number = data.get('award_number')
    
    if title_keyword:
        query = f"Find works related to '{title_keyword}'"
    elif award_number:
        query = f"Find works funded by '{award_number}'"
    else:
        return jsonify({"error": "Provide title_keyword or award_number"})
    
    response = agent.query(query)
    return jsonify({"results": str(response)})
```

### 2. Research Dashboard Integration
```python
class ResearchDashboard:
    def __init__(self):
        self.agent = WorkBasedRelationshipAgent(ConfigManager())
    
    def get_work_relationships(self, work_identifier):
        """Get all relationships for a work."""
        query = f"Find all works related to '{work_identifier}' through any relationship type"
        return self.agent.query(query)
    
    def get_funding_portfolio(self, award_number):
        """Get all works from a funding source."""
        query = f"Find all works funded by award number '{award_number}'"
        return self.agent.query(query)
    
    def expand_literature_review(self, research_topic):
        """Expand literature review with related works."""
        query = f"Find works related to '{research_topic}' for literature review"
        return self.agent.query(query)
```

### 3. Batch Processing
```python
def process_work_list(work_titles):
    """Process a list of works to find all relationships."""
    agent = WorkBasedRelationshipAgent(ConfigManager())
    results = {}
    
    for title in work_titles:
        try:
            query = f"Find all works related to '{title}'"
            response = agent.query(query)
            results[title] = response
        except Exception as e:
            results[title] = {"error": str(e)}
    
    return results
```

## Performance Considerations

### 1. Query Optimization
- Use specific keywords rather than very broad terms
- Limit results with LIMIT clauses for large datasets
- Use indexed fields (id, title) when possible

### 2. Caching Strategy
```python
from functools import lru_cache

class CachedWorkAgent:
    def __init__(self):
        self.agent = WorkBasedRelationshipAgent(ConfigManager())
    
    @lru_cache(maxsize=100)
    def cached_query(self, query_string):
        return self.agent.query(query_string)
```

### 3. Batch Operations
- Group similar queries together
- Use comprehensive queries instead of multiple specific ones
- Process results in batches for large datasets

## Error Handling

### Common Error Patterns
```python
def safe_work_discovery(query):
    try:
        agent = WorkBasedRelationshipAgent(ConfigManager())
        response = agent.query(query)
        
        # Check for error indicators in response
        response_str = str(response)
        if "error" in response_str.lower():
            return {"status": "error", "message": "Query execution failed"}
        
        return {"status": "success", "data": response}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### Validation
```python
def validate_work_input(title_keyword=None, award_number=None):
    """Validate input parameters."""
    if not title_keyword and not award_number:
        raise ValueError("Either title_keyword or award_number must be provided")
    
    if title_keyword and len(title_keyword.strip()) < 3:
        raise ValueError("Title keyword must be at least 3 characters")
    
    if award_number and not re.match(r'^[A-Z0-9\-]+$', award_number):
        raise ValueError("Invalid award number format")
```

## Best Practices

### 1. Query Design
- Start with specific keywords and broaden if needed
- Use relationship type hints ("through shared authors")
- Combine multiple discovery methods for comprehensive results

### 2. Result Processing
- Always check for error indicators in responses
- Extract key insights from enhanced_analysis
- Use relationship_type to understand connection strength

### 3. User Experience
- Provide clear feedback about what relationships were found
- Show relationship strength indicators
- Offer suggestions for refining searches

### 4. Data Quality
- Validate input parameters
- Handle missing or incomplete data gracefully
- Provide meaningful error messages

## Conclusion

The work-based relationship discovery system enables powerful GraphRAG capabilities by allowing users to:

1. **Input work titles or award numbers** as starting points
2. **Discover related works** through multiple relationship types
3. **Analyze research portfolios** comprehensively
4. **Expand literature reviews** systematically
5. **Track funding impact** effectively

This supports the project's goal of enhancing document summarization for research portfolio development through graph-based AI techniques.