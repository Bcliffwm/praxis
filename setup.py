"""
Setup script for Research GraphRAG package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Research GraphRAG - Graph-based research analysis and summarization toolkit"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="research-graph-rag",
    version="1.0.0",
    author="Research GraphRAG Team",
    author_email="research@example.com",
    description="Graph-based research analysis and summarization toolkit",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/research-graph-rag",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "jupyter": [
            "jupyter>=1.0.0",
            "ipykernel>=6.0.0",
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
        ],
        "streamlit": [
            "streamlit>=1.28.0",
            "plotly>=5.0.0",
            "streamlit-agraph>=0.0.45",
        ]
    },
    entry_points={
        "console_scripts": [
            "research-graph-rag=research_graph_rag.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "research_graph_rag": [
            "utils/*.py",
            "agents/*.py", 
            "core/*.py",
        ],
    },
    zip_safe=False,
)