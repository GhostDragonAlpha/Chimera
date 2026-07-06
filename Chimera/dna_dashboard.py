import json
import re
import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")
PENDING_HEURISTICS_PATH = DNA_GRAPH_PATH.parent / "PENDING_HEURISTICS.md"
sys.path.insert(0, str(DNA_GRAPH_PATH.parent.parent))

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

# --- Generation Protocol: Inheritance Log (the morning funeral meeting) ---
st.subheader("🌅 Inheritance Log — Generation Protocol")
try:
    from core.graphify_interface import collect_inheritance
    inh = collect_inheritance(nodes)
except Exception:
    inh = {"will": None, "open_pains": []}

col_will, col_pains, col_dream = st.columns(3)
with col_will:
    st.markdown("**The Will (latest)**")
    if inh["will"]:
        st.info(f"{inh['will']['inheritance']}\n\n— {inh['will']['phase'][:60]} "
                f"@ {inh['will']['timestamp'][:19]}")
    else:
        st.caption("No inheritance recorded yet (postflight --inheritance).")
with col_pains:
    st.markdown("**Open phantom pains**")
    if inh["open_pains"]:
        for p in inh["open_pains"][:6]:
            st.warning(f"`{p['id']}` [{p['age_days']}d] {p['text']}")
    else:
        st.caption("All inherited pains dispositioned.")
with col_dream:
    st.markdown("**Dream Report — awaiting the Gardener**")
    if PENDING_HEURISTICS_PATH.exists():
        text = PENDING_HEURISTICS_PATH.read_text(encoding="utf-8")
        entries = re.findall(r"^## (H-\d+): (.+?)$\n- status: (\w+)", text, re.MULTILINE)
        pending = [(n, s) for n, s, status in entries if status == "pending"]
        promoted = sum(1 for _, _, status in entries if status == "promoted")
        st.metric("Pending heuristics", len(pending), delta=f"{promoted} promoted all-time")
        for num, sig in pending[:6]:
            st.caption(f"**{num}** {sig}")
    else:
        st.caption("No candidates distilled yet (python -m core.dream_loop).")

# --- Generation Protocol: the sawtooth — grade scores over time ---
st.subheader("📈 Grade Sawtooth — score per ProfessorGrade over time")
grade_nodes = [n for n in nodes if n.get("type") == "ProfessorGrade" and n.get("timestamp")]
if grade_nodes:
    import pandas as pd
    rows = []
    for n in grade_nodes:
        m = re.search(r"(\d{1,3}(?:\.\d)?)\s*/\s*100", str(n.get("reasoning", "")))
        score = float(m.group(1)) if m else {"A": 95, "B": 82, "C": 67, "F": 40}.get(
            str(n.get("grade", "")).upper(), None)
        if score is not None:
            rows.append({"timestamp": n["timestamp"], "score": score,
                         "feature": n.get("feature", n.get("feature_name", "?")),
                         "grade": str(n.get("grade", "?")).upper()})
    if rows:
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", utc=True)
        df = df.sort_values("timestamp")
        fig_saw = px.line(df, x="timestamp", y="score", markers=True,
                          hover_data=["feature", "grade"],
                          title="Dips are paid tuition; each recovery should crest higher")
        fig_saw.add_hline(y=90, line_dash="dot", annotation_text="A")
        fig_saw.add_hline(y=60, line_dash="dot", annotation_text="C floor")
        st.plotly_chart(fig_saw, use_container_width=True)
else:
    st.caption("No grades recorded yet.")

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
