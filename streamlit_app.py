"""
Streamlit application for Research GraphRAG.

Interactive web interface for research analysis and visualization.
"""

import streamlit as st
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List

# Import the research_graph_rag package
try:
    from research_graph_rag import (
        ConfigManager, ResearchQueryAgent, EnhancedResearchQueryAgent,
        NetworkAnalysisAgent, WorkBasedDiscoveryAgent
    )
except ImportError as e:
    st.error(f"Failed to import research_graph_rag package: {e}")
    st.stop()


# Page configuration
st.set_page_config(
    page_title="Research GraphRAG",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_config():
    """Initialize configuration manager."""
    try:
        return ConfigManager()
    except Exception as e:
        st.error(f"Failed to initialize configuration: {e}")
        return None


@st.cache_resource
def initialize_agents(_config_manager):
    """Initialize all agent types."""
    if not _config_manager:
        return {}
    
    try:
        agents = {
            "Base Agent": ResearchQueryAgent(_config_manager),
            "Relationship Agent": EnhancedResearchQueryAgent(_config_manager),
            "Network Analysis Agent": NetworkAnalysisAgent(_config_manager),
            "Work Discovery Agent": WorkBasedDiscoveryAgent(_config_manager)
        }
        return agents
    except Exception as e:
        st.error(f"Failed to initialize agents: {e}")
        return {}


def display_database_info(agent):
    """Display database information."""
    with st.spinner("Getting database information..."):
        info = agent.get_database_info()
    
    if "error" in info:
        st.error(f"Database Error: {info['error']}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Database Details")
        st.write(f"**Database:** {info.get('database', 'Unknown')}")
        st.write(f"**URI:** {info.get('uri', 'Unknown')}")
        st.write(f"**GDS Available:** {'✅' if info.get('gds_available') else '❌'}")
    
    with col2:
        st.subheader("Connection Status")
        test_result = agent.test_connection()
        if test_result.get('status') == 'success':
            st.success("✅ Database connection successful")
        else:
            st.error(f"❌ Connection failed: {test_result.get('message')}")
    
    # Node counts
    if 'nodes' in info and info['nodes']:
        st.subheader("Node Counts")
        node_data = []
        for node_info in info['nodes']:
            labels = ', '.join(node_info.get('labels', []))
            count = node_info.get('count', 0)
            node_data.append({"Node Type": labels, "Count": count})
        
        if node_data:
            df_nodes = pd.DataFrame(node_data)
            fig_nodes = px.bar(df_nodes, x="Node Type", y="Count", 
                             title="Node Distribution")
            st.plotly_chart(fig_nodes, use_container_width=True)
    
    # Relationship counts
    if 'relationships' in info and info['relationships']:
        st.subheader("Relationship Counts")
        rel_data = []
        for rel_info in info['relationships']:
            rel_type = rel_info.get('relationship_type', 'Unknown')
            count = rel_info.get('count', 0)
            rel_data.append({"Relationship Type": rel_type, "Count": count})
        
        if rel_data:
            df_rels = pd.DataFrame(rel_data)
            fig_rels = px.bar(df_rels, x="Relationship Type", y="Count",
                            title="Relationship Distribution")
            st.plotly_chart(fig_rels, use_container_width=True)


def display_query_results(results: Dict[str, Any]):
    """Display query results in a formatted way."""
    if isinstance(results, str):
        st.write(results)
        return
    
    if isinstance(results, dict):
        if "error" in results:
            st.error(f"Query Error: {results['error']}")
            return
        
        # Display structured results
        for key, value in results.items():
            if key == "records" and isinstance(value, list):
                if value:
                    st.subheader("Query Results")
                    df = pd.DataFrame(value)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No records found")
            elif key == "row_count":
                st.metric("Records Found", value)
            elif isinstance(value, (dict, list)):
                with st.expander(f"View {key.replace('_', ' ').title()}"):
                    st.json(value)
            else:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")


def network_analysis_page():
    """Network analysis page."""
    st.header("🕸️ Network Analysis")
    
    config_manager = initialize_config()
    if not config_manager:
        return
    
    agents = initialize_agents(config_manager)
    if "Network Analysis Agent" not in agents:
        st.error("Network Analysis Agent not available")
        return
    
    network_agent = agents["Network Analysis Agent"]
    
    # Analysis options
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Centrality Metrics", "Community Detection", "Related Works Discovery"]
    )
    
    if analysis_type == "Centrality Metrics":
        st.subheader("Centrality Metrics Analysis")
        limit = st.slider("Number of results", 5, 50, 20)
        
        if st.button("Run Centrality Analysis"):
            with st.spinner("Running centrality analysis..."):
                results = network_agent.get_centrality_metrics(limit=limit)
            
            if "error" not in results:
                metrics = results.get("metrics", {})
                
                # Create tabs for different centrality measures
                tabs = st.tabs(list(metrics.keys()))
                
                for i, (metric_name, metric_data) in enumerate(metrics.items()):
                    with tabs[i]:
                        if "records" in metric_data and metric_data["records"]:
                            df = pd.DataFrame(metric_data["records"])
                            st.dataframe(df, use_container_width=True)
                            
                            # Create visualization
                            if len(df) > 0:
                                score_col = [col for col in df.columns if 'score' in col.lower() or 'centrality' in col.lower()]
                                if score_col:
                                    fig = px.bar(df.head(10), x="title", y=score_col[0],
                                               title=f"Top 10 Works by {metric_name.replace('_', ' ').title()}")
                                    fig.update_xaxes(tickangle=45)
                                    st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info(f"No data available for {metric_name}")
            else:
                st.error(f"Analysis failed: {results['error']}")
    
    elif analysis_type == "Community Detection":
        st.subheader("Community Detection")
        
        if st.button("Detect Communities"):
            with st.spinner("Detecting communities..."):
                results = network_agent.detect_communities()
            
            if "error" not in results:
                result_data = results.get("result", {})
                
                # Display community statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Communities", result_data.get("total_communities", 0))
                with col2:
                    st.metric("Total Works", result_data.get("total_works", 0))
                with col3:
                    st.metric("Largest Community", result_data.get("largest_community_size", 0))
                
                # Display community details
                communities = result_data.get("communities", [])
                if communities:
                    st.subheader("Community Details")
                    
                    for community in communities[:10]:  # Show top 10 communities
                        with st.expander(f"Community {community['community_id']} ({community['size']} works)"):
                            works_df = pd.DataFrame(community['works'])
                            st.dataframe(works_df, use_container_width=True)
            else:
                st.error(f"Community detection failed: {results['error']}")
    
    elif analysis_type == "Related Works Discovery":
        st.subheader("Related Works Discovery")
        
        title_keyword = st.text_input("Enter title keyword:")
        limit = st.slider("Number of results", 5, 50, 20)
        
        if st.button("Find Related Works") and title_keyword:
            with st.spinner("Finding related works..."):
                results = network_agent.find_related_by_network_analysis(
                    title_keyword=title_keyword,
                    limit=limit
                )
            
            if "error" not in results:
                analysis_results = results.get("results", {})
                
                # Create tabs for different analysis types
                if analysis_results:
                    tabs = st.tabs(list(analysis_results.keys()))
                    
                    for i, (analysis_name, analysis_data) in enumerate(analysis_results.items()):
                        with tabs[i]:
                            if "records" in analysis_data and analysis_data["records"]:
                                df = pd.DataFrame(analysis_data["records"])
                                st.dataframe(df, use_container_width=True)
                                
                                # Visualization for confidence scores
                                if "confidence_score" in df.columns:
                                    fig = px.scatter(df, x="related_work_title", y="confidence_score",
                                                   title=f"Confidence Scores - {analysis_name.replace('_', ' ').title()}")
                                    fig.update_xaxes(tickangle=45)
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info(f"No results for {analysis_name}")
            else:
                st.error(f"Analysis failed: {results['error']}")


def query_interface_page():
    """Query interface page."""
    st.header("💬 Query Interface")
    
    config_manager = initialize_config()
    if not config_manager:
        return
    
    agents = initialize_agents(config_manager)
    if not agents:
        return
    
    # Agent selection
    agent_name = st.selectbox("Select Agent", list(agents.keys()))
    selected_agent = agents[agent_name]
    
    # Query input
    query = st.text_area("Enter your research query:", height=100)
    
    if st.button("Execute Query") and query:
        with st.spinner("Processing query..."):
            try:
                response = selected_agent.query(query)
                st.subheader("Query Response")
                display_query_results(response)
            except Exception as e:
                st.error(f"Query execution failed: {e}")


def main():
    """Main Streamlit application."""
    st.markdown('<h1 class="main-header">🔬 Research GraphRAG</h1>', unsafe_allow_html=True)
    st.markdown("**Graph-based Research Analysis and Summarization Toolkit**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Database Overview", "Query Interface", "Network Analysis", "Work Discovery"]
    )
    
    # Initialize configuration
    config_manager = initialize_config()
    if not config_manager:
        st.error("Failed to initialize configuration. Please check your .env file.")
        return
    
    # Page routing
    if page == "Database Overview":
        st.header("📊 Database Overview")
        agents = initialize_agents(config_manager)
        if agents:
            base_agent = list(agents.values())[0]  # Use any agent for database info
            display_database_info(base_agent)
    
    elif page == "Query Interface":
        query_interface_page()
    
    elif page == "Network Analysis":
        network_analysis_page()
    
    elif page == "Work Discovery":
        st.header("🔍 Work Discovery")
        st.info("Work discovery interface coming soon...")
    
    # Sidebar information
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown(
        "Research GraphRAG uses Neo4j graph database and AWS Bedrock "
        "to provide advanced research analysis capabilities."
    )
    
    st.sidebar.markdown("### Configuration")
    if config_manager:
        config_dict = config_manager.to_dict()
        st.sidebar.success("✅ Configuration loaded")
        with st.sidebar.expander("View Config"):
            st.json(config_dict)
    else:
        st.sidebar.error("❌ Configuration failed")


if __name__ == "__main__":
    main()