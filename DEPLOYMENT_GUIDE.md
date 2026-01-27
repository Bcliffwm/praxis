# Research GraphRAG Deployment Guide

This guide covers deployment options for the Research GraphRAG package, including Streamlit applications, production environments, and development setups.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Streamlit Deployment](#streamlit-deployment)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration Management](#configuration-management)
7. [Monitoring and Logging](#monitoring-and-logging)

## Development Setup

### Prerequisites

- Python 3.12+
- Poetry (recommended) or pip
- Neo4j database (local or cloud)
- AWS account with Bedrock access

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd research-graph-rag
   
   # Using Poetry (recommended)
   poetry install --extras "dev streamlit jupyter"
   poetry shell
   
   # Or using pip
   pip install -e ".[dev,streamlit,jupyter]"
   ```

2. **Environment Configuration**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

3. **Database Setup**
   ```bash
   # Start Neo4j (if running locally)
   neo4j start
   
   # Test connection
   research-graph-rag test
   ```

4. **Development Server**
   ```bash
   # Start Streamlit app
   streamlit run streamlit_app.py
   
   # Or start Jupyter
   jupyter notebook
   ```

## Streamlit Deployment

### Local Streamlit

```bash
# Install with Streamlit extras
pip install -e ".[streamlit]"

# Run the application
streamlit run streamlit_app.py --server.port 8501
```

### Streamlit Cloud

1. **Prepare Repository**
   ```bash
   # Ensure requirements.txt is up to date
   pip freeze > requirements.txt
   
   # Create streamlit config
   mkdir -p .streamlit
   cat > .streamlit/config.toml << EOF
   [server]
   headless = true
   port = 8501
   
   [theme]
   primaryColor = "#1f77b4"
   backgroundColor = "#ffffff"
   secondaryBackgroundColor = "#f0f2f6"
   textColor = "#262730"
   EOF
   ```

2. **Deploy to Streamlit Cloud**
   - Push code to GitHub
   - Connect repository to Streamlit Cloud
   - Set environment variables in Streamlit Cloud dashboard
   - Deploy application

### Streamlit with Docker

```dockerfile
# Dockerfile for Streamlit
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Production Deployment

### Using Gunicorn + Flask

Create a Flask wrapper for production:

```python
# app.py
from flask import Flask, request, jsonify
from research_graph_rag import ConfigManager, ResearchQueryAgent

app = Flask(__name__)
config_manager = ConfigManager()
agent = ResearchQueryAgent(config_manager)

@app.route('/health')
def health():
    return {'status': 'healthy'}

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    query_text = data.get('query')
    
    try:
        response = agent.query(query_text)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
```

Deploy with Gunicorn:
```bash
# Install Gunicorn
pip install gunicorn

# Run production server
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

### Using FastAPI

```python
# fastapi_app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from research_graph_rag import ConfigManager, ResearchQueryAgent

app = FastAPI(title="Research GraphRAG API")
config_manager = ConfigManager()
agent = ResearchQueryAgent(config_manager)

class QueryRequest(BaseModel):
    query: str
    agent_type: str = "base"

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/query")
def query_endpoint(request: QueryRequest):
    try:
        response = agent.query(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

## Docker Deployment

### Multi-stage Dockerfile

```dockerfile
# Multi-stage Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Install the package
RUN pip install --no-deps -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Default command
CMD ["python", "-m", "research_graph_rag.cli", "--help"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.15-community
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["graph-data-science"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

  research-graphrag:
    build: .
    environment:
      DB_URI: bolt://neo4j:7687
      DB_USER: neo4j
      DB_PASSWORD: password
      TARGET_DB: neo4j
    depends_on:
      - neo4j
    ports:
      - "8501:8501"
    command: streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0

volumes:
  neo4j_data:
  neo4j_logs:
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name research-graphrag
   ```

2. **Build and Push Image**
   ```bash
   # Get login token
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build and tag image
   docker build -t research-graphrag .
   docker tag research-graphrag:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/research-graphrag:latest

   # Push image
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/research-graphrag:latest
   ```

3. **ECS Task Definition**
   ```json
   {
     "family": "research-graphrag",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "research-graphrag",
         "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/research-graphrag:latest",
         "portMappings": [
           {
             "containerPort": 8501,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DB_URI",
             "value": "bolt://your-neo4j-instance:7687"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/research-graphrag",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

#### Using AWS Lambda

For serverless deployment:

```python
# lambda_handler.py
import json
from research_graph_rag import ConfigManager, ResearchQueryAgent

# Initialize outside handler for reuse
config_manager = ConfigManager()
agent = ResearchQueryAgent(config_manager)

def lambda_handler(event, context):
    try:
        query = event.get('query')
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Query parameter required'})
            }
        
        response = agent.query(query)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'response': response})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Google Cloud Platform

#### Using Cloud Run

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/research-graphrag', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/research-graphrag']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'research-graphrag'
      - '--image'
      - 'gcr.io/$PROJECT_ID/research-graphrag'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
```

## Configuration Management

### Environment-specific Configurations

```python
# config/production.py
import os

class ProductionConfig:
    DB_URI = os.getenv('DB_URI')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    TARGET_DB = os.getenv('TARGET_DB', 'praxis')
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    REGION_NAME = os.getenv('REGION_NAME', 'us-east-1')
    
    # Application settings
    DEBUG = False
    LOG_LEVEL = 'INFO'
    MAX_QUERY_TIMEOUT = 30
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-graphrag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: research-graphrag
  template:
    metadata:
      labels:
        app: research-graphrag
    spec:
      containers:
      - name: research-graphrag
        image: research-graphrag:latest
        ports:
        - containerPort: 8501
        env:
        - name: DB_URI
          valueFrom:
            secretKeyRef:
              name: research-graphrag-secrets
              key: db-uri
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: research-graphrag-secrets
              key: db-password
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: research-graphrag-service
spec:
  selector:
    app: research-graphrag
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
  type: LoadBalancer
```

## Monitoring and Logging

### Application Monitoring

```python
# monitoring.py
import logging
import time
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logging.info(f"{func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper
```

### Health Checks

```python
# health.py
from research_graph_rag import ConfigManager, ResearchQueryAgent

def health_check():
    """Comprehensive health check for the application."""
    checks = {
        'database': False,
        'aws': False,
        'configuration': False
    }
    
    try:
        # Test configuration
        config_manager = ConfigManager()
        checks['configuration'] = True
        
        # Test database connection
        agent = ResearchQueryAgent(config_manager)
        db_test = agent.test_connection()
        checks['database'] = db_test.get('status') == 'success'
        
        # Test AWS connection (basic)
        aws_config = config_manager.get_aws_config()
        checks['aws'] = bool(aws_config.get('aws_access_key_id'))
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
    
    return {
        'status': 'healthy' if all(checks.values()) else 'unhealthy',
        'checks': checks
    }
```

## Security Considerations

1. **Environment Variables**: Never commit sensitive data to version control
2. **Network Security**: Use VPCs and security groups in cloud deployments
3. **Authentication**: Implement proper authentication for production APIs
4. **Input Validation**: Always validate and sanitize user inputs
5. **Rate Limiting**: Implement rate limiting for public APIs
6. **Logging**: Avoid logging sensitive information

## Performance Optimization

1. **Connection Pooling**: Use connection pooling for Neo4j
2. **Caching**: Implement caching for frequently accessed data
3. **Async Processing**: Use async processing for long-running queries
4. **Resource Limits**: Set appropriate resource limits in containers
5. **Monitoring**: Monitor performance metrics and optimize bottlenecks

## Troubleshooting

### Common Issues

1. **Database Connection Failures**
   - Check Neo4j service status
   - Verify connection credentials
   - Test network connectivity

2. **AWS Authentication Errors**
   - Verify AWS credentials
   - Check IAM permissions
   - Confirm Bedrock service availability

3. **Memory Issues**
   - Increase container memory limits
   - Optimize query complexity
   - Implement result pagination

4. **Performance Problems**
   - Enable query profiling
   - Optimize Cypher queries
   - Check database indexes