import streamlit as st
import json
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")

st.set_page_config(page_title="Chimera DNA Dashboard", page_icon="🧬", layout="wide")

def load_dna_graph():
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}

st.title("🧬 Chimera DNA Dashboard - Graphify Knowledge Graph")

graph = load_dna_graph()
nodes = graph.get("nodes", [])
edges = graph.get("edges", [])

# Metrics row
mutations = [n for n in nodes if n["type"] == "Mutation"]
errors = [n for n in nodes if n["type"] == "Error"]
fixes = [n for n in nodes if n["type"] == "Fix"]
health_nodes = [n for n in nodes if n["type"] == "Health"]

total_mutations = len(mutations)
successful_compilations = sum(1 for m in mutations if m.get("compilation_result") == "pass")
success_rate = (successful_compilations / total_mutations * 100) if total_mutations > 0 else 100.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Mutations Recorded", total_mutations)
with col2:
    st.metric("Compilation Success Rate", f"{success_rate:.1f}%")
with col3:
    st.metric("Known Errors", len(errors))
with col4:
    st.metric("Applied Fixes", len(fixes))

# Error categories
st.subheader("Error Categories")
error_categories = {}
for fix in fixes:
    cats = fix.get("categories", [])
    for cat in cats:
        error_categories[cat] = error_categories.get(cat, 0) + 1

if error_categories:
    cat_df = __import__('pandas').DataFrame(list(error_categories.items()), columns=['Category', 'Count'])
    fig_cat = px.bar(cat_df, x='Category', y='Count', title='Most Common Error Categories')
    st.plotly_chart(fig_cat, use_container_width=True)

# Templates with most mutations
st.subheader("Templates with Most Mutations (Fragile Templates)")
template_counts = {}
for m in mutations:
    tf = m.get('template_file', 'unknown')
    template_counts[tf] = template_counts.get(tf, 0) + 1

if template_counts:
    temp_df = __import__('pandas').DataFrame(list(template_counts.items()), columns=['Template', 'Mutation_Count'])
    temp_df = temp_df.sort_values(by='Mutation_Count', ascending=False).head(10)
    fig_temp = px.bar(temp_df, x='Template', y='Mutation_Count', title='Most Fragile Templates')
    st.plotly_chart(fig_temp, use_container_width=True)

# DNA Graph Visualization
st.subheader("DNA Knowledge Graph")

node_types = {}
for n in nodes:
    t = n.get('type', 'Unknown')
    node_types[t] = node_types.get(t, 0) + 1

fig_nodes = go.Figure()
for nt, count in node_types.items():
    fig_nodes.add_trace(go.Pie(labels=[nt], values=[count], name=nt))

st.plotly_chart(fig_nodes, use_container_width=True)

# Recent fixes and status
st.subheader("Recent Fixes")
recent_fixes = sorted(fixes, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
for fix in recent_fixes:
    st.caption(f"**{fix.get('fix_description', 'Unknown Fix')}** - Categories: {', '.join(fix.get('categories', []))}")

# Error trend over time
st.subheader("Error Trend Over Time")
error_timestamps = [e.get('timestamp', '') for e in errors if e.get('timestamp')]
if error_timestamps:
    import pandas as pd
    df_errors = pd.DataFrame({'timestamp': error_timestamps})
    df_errors['date'] = pd.to_datetime(df_errors['timestamp']).dt.date
    error_trends = df_errors.groupby('date').size().reset_index(name='count')
    
    fig_trend = px.line(error_trends, x='date', y='count', title='Errors Over Time (Should Trend to Zero)')
    st.plotly_chart(fig_trend, use_container_width=True)
