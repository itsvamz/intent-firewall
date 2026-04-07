"""
IntentShield Dashboard
Full visualization of the Intent Graph Firewall in action.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from datetime import datetime

from core.intent_parser import parse_intent
from core.graph_builder import build_intent_graph, graph_to_dict
from core.armorclaw import ArmorClaw
from agent.agent import OpenClawAgent

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntentShield | ArmorClaw",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0a0e1a;
        color: #e2e8f0;
    }
    .main { background-color: #0a0e1a; }
    .stApp { background-color: #0a0e1a; }

    .verdict-allow {
        background: linear-gradient(135deg, #0d4a1f, #1a7a35);
        border: 1px solid #2ecc71;
        border-radius: 10px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
    }
    .verdict-block {
        background: linear-gradient(135deg, #4a0d0d, #7a1a1a);
        border: 1px solid #e74c3c;
        border-radius: 10px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
    }
    .layer-card {
        background: #131929;
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        border-left: 3px solid #3b82f6;
    }
    .layer-card-fail {
        background: #1a0d0d;
        border-radius: 8px;
        padding: 12px;
        margin: 6px 0;
        border-left: 3px solid #ef4444;
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-box {
        background: #131929;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #1e2d4a;
    }
    .risk-bar-container {
        background: #1e2d3a;
        border-radius: 20px;
        height: 12px;
        overflow: hidden;
        margin: 8px 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }
    .stSelectbox > div, .stTextInput > div > div {
        background: #131929 !important;
        border: 1px solid #1e2d4a !important;
        color: #e2e8f0 !important;
    }
    h1, h2, h3 {
        color: #e2e8f0 !important;
    }
    .stSidebar {
        background-color: #0d1220 !important;
    }
    .stSidebar > div {
        background-color: #0d1220 !important;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .log-entry {
        background: #0d1525;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 4px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        border-left: 3px solid #475569;
    }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ────────────────────────────────────────────────────────
if "enforcement_log" not in st.session_state:
    st.session_state.enforcement_log = []
if "armor" not in st.session_state:
    st.session_state.armor = ArmorClaw()
if "current_graph" not in st.session_state:
    st.session_state.current_graph = None
if "current_intent" not in st.session_state:
    st.session_state.current_intent = None

# ── Helper Functions ──────────────────────────────────────────────────────────
def draw_intent_graph(G: nx.DiGraph, enforcement_results: list = None):
    fig, ax = plt.subplots(1, 1, figsize=(12, 3))
    fig.patch.set_facecolor('#0a0e1a')
    ax.set_facecolor('#0a0e1a')

    blocked_steps = set()
    allowed_steps = set()
    if enforcement_results:
        for r in enforcement_results:
            if r["verdict"] == "BLOCK":
                blocked_steps.add(r["next_step"])
            else:
                allowed_steps.add(r["next_step"])

    pos = nx.spring_layout(G, k=3, seed=42)
    # Use hierarchical layout for linear graphs
    nodes = list(G.nodes())
    pos = {node: (i * 2.5, 0) for i, node in enumerate(nodes)}

    node_colors = []
    for node in G.nodes():
        if node in blocked_steps:
            node_colors.append("#e74c3c")
        elif node in allowed_steps:
            node_colors.append("#2ecc71")
        elif node == "START":
            node_colors.append("#3b82f6")
        elif node == "END":
            node_colors.append("#8b5cf6")
        else:
            node_colors.append("#475569")

    labels = {}
    for node in G.nodes():
        label = node.replace("_", "\n")
        labels[node] = label

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1200,
                           alpha=0.9, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7,
                            font_color="white", font_weight="bold", ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color="#3b82f6", arrows=True,
                           arrowsize=20, width=2.0,
                           connectionstyle="arc3,rad=0.1", ax=ax)

    legend_patches = [
        mpatches.Patch(color="#3b82f6", label="Start"),
        mpatches.Patch(color="#2ecc71", label="Allowed"),
        mpatches.Patch(color="#e74c3c", label="Blocked"),
        mpatches.Patch(color="#8b5cf6", label="End"),
        mpatches.Patch(color="#475569", label="Pending"),
    ]
    ax.legend(handles=legend_patches, loc="upper right",
              facecolor="#131929", edgecolor="#1e2d4a",
              labelcolor="white", fontsize=8)
    ax.axis("off")
    plt.tight_layout()
    return fig

def risk_color(score: float) -> str:
    if score < 0.35:
        return "#2ecc71"
    elif score < 0.65:
        return "#f39c12"
    else:
        return "#e74c3c"

def render_enforcement_result(result: dict):
    verdict = result["verdict"]
    is_block = verdict == "BLOCK"
    card_class = "verdict-block" if is_block else "verdict-allow"
    icon = "🚫" if is_block else "✅"
    color = "#ef4444" if is_block else "#22c55e"

    with st.container():
        st.markdown(f"""
        <div class="{card_class}">
            <b style="font-size:1.1rem; color:{color};">{icon} {verdict}</b>
            &nbsp;|&nbsp; <span style="color:#94a3b8">{result['current_step']} → {result['next_step']}</span>
            &nbsp;|&nbsp; <span style="color:#64748b; font-size:0.85rem">ID: {result['verdict_id']}</span>
            {f'<br><span style="color:#ef4444; font-size:0.9rem; margin-top:4px; display:block">⚠ {result["block_reason"]}</span>' if is_block else ''}
        </div>
        """, unsafe_allow_html=True)

    # Layer breakdown
    cols = st.columns(4)
    for i, check in enumerate(result["checks"]):
        with cols[i]:
            sym = "✓" if check["passed"] else "✗"
            color = "#22c55e" if check["passed"] else "#ef4444"
            bg = "#0d2818" if check["passed"] else "#1a0d0d"
            st.markdown(f"""
            <div style="background:{bg}; border-radius:8px; padding:10px; text-align:center; border:1px solid {color}33; margin:2px">
                <div style="color:{color}; font-size:1.2rem; font-weight:700">{sym}</div>
                <div style="font-size:0.7rem; color:#94a3b8; font-family:'JetBrains Mono',monospace">Layer {check['layer']}</div>
                <div style="font-size:0.72rem; color:#e2e8f0; font-weight:600">{check['name']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Risk score
    rscore = result.get("risk_score", 0)
    rcolor = risk_color(rscore)
    st.markdown(f"""
    <div style="margin: 4px 0 12px 0;">
        <span style="font-size:0.8rem; color:#94a3b8">Risk Score: </span>
        <span style="color:{rcolor}; font-weight:700; font-family:'JetBrains Mono',monospace">{rscore:.3f}</span>
        <span style="font-size:0.75rem; color:#475569"> / 1.000</span>
    </div>
    """, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## IntentShield")
    st.markdown("*Intent Graph Firewall for Autonomous Financial Agents*")
    st.divider()

    st.markdown("### ⚙️ Configuration")

    adversarial = st.toggle("Inject Adversarial Action", value=False,
                            help="Simulate a rogue action mid-pipeline")
    inject_at = st.slider("Inject at Step", 0, 3, 1, disabled=not adversarial)
    agent_role = st.selectbox("Agent Role (Delegation)",
                              ["None (Direct)", "research_agent", "trade_agent"])
    role = None if agent_role == "None (Direct)" else agent_role

    st.divider()
    st.markdown("### 🧪 Quick Scenarios")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 Safe Analyze"):
            st.session_state["quick_input"] = "Analyze Tesla stock"
            st.session_state["quick_adversarial"] = False
    with col2:
        if st.button("🔴 Rogue Trade"):
            st.session_state["quick_input"] = "Analyze Tesla stock"
            st.session_state["quick_adversarial"] = True

    col3, col4 = st.columns(2)
    with col3:
        if st.button("Oversize Buy"):
            st.session_state["quick_input"] = "Buy $50000 of TSLA"
            st.session_state["quick_adversarial"] = False
    with col4:
        if st.button("Research→Trade"):
            st.session_state["quick_input"] = "Buy AAPL"
            st.session_state["quick_adversarial"] = False
            st.session_state["quick_role"] = "research_agent"

    st.divider()
    if st.button("Clear Session"):
        st.session_state.enforcement_log = []
        st.session_state.armor = ArmorClaw()
        st.session_state.current_graph = None
        st.rerun()

    st.markdown("### Session Stats")
    total = len(st.session_state.enforcement_log)
    allowed_count = sum(1 for r in st.session_state.enforcement_log if r["verdict"] == "ALLOW")
    blocked_count = total - allowed_count
    st.metric("Total Enforcements", total)
    st.metric("✅ Allowed", allowed_count)
    st.metric("🚫 Blocked", blocked_count)

# ── Main Content ──────────────────────────────────────────────────────────────
st.markdown('<div class="header-title"> IntentShield | ArmorClaw</div>', unsafe_allow_html=True)
st.markdown("*Intent Graph Firewall for Autonomous Financial Agents*")
st.divider()

# Input area
quick_input = st.session_state.pop("quick_input", "")
quick_adversarial = st.session_state.pop("quick_adversarial", adversarial)
quick_role = st.session_state.pop("quick_role", role)

col_input, col_btn = st.columns([4, 1])
with col_input:
    user_input = st.text_input(
        "Agent Instruction",
        value=quick_input or "",
        placeholder="e.g. Analyze Tesla stock | Buy $5000 of AAPL | Monitor portfolio",
        label_visibility="visible"
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶ ENFORCE")

# ── Run pipeline ──────────────────────────────────────────────────────────────
if run_btn and user_input.strip():
    use_adversarial = quick_adversarial
    use_role = quick_role if quick_role else role

    with st.spinner("Running Intent Graph Firewall..."):
        # Parse
        intent = parse_intent(user_input)
        G = build_intent_graph(intent["allowed_steps"])
        agent = OpenClawAgent(name="FinAgent-Alpha", role=use_role)
        planned = agent.plan_actions(intent, adversarial=use_adversarial, inject_at=inject_at)

        armor = st.session_state.armor
        new_results = []

        for step_plan in planned:
            current = step_plan["current"]
            nxt = step_plan["next"]
            action = step_plan["action"]
            if use_role:
                action["agent_role"] = use_role

            result = armor.enforce(action, G, current, nxt)
            new_results.append(result)
            st.session_state.enforcement_log.extend(new_results)

        st.session_state.current_graph = G
        st.session_state.current_intent = intent
        st.session_state.current_results = new_results

# ── Display Results ───────────────────────────────────────────────────────────
if "current_results" in st.session_state and st.session_state.current_results:
    results = st.session_state.current_results
    intent = st.session_state.current_intent
    G = st.session_state.current_graph

    # Intent summary
    st.markdown("### Parsed Intent")
    icols = st.columns(4)
    with icols[0]:
        st.markdown(f"""<div class="metric-box"><div style="color:#64748b;font-size:0.8rem">INTENT</div>
        <div style="font-size:1.1rem;font-weight:700;color:#3b82f6">{intent['label']}</div></div>""",
        unsafe_allow_html=True)
    with icols[1]:
        st.markdown(f"""<div class="metric-box"><div style="color:#64748b;font-size:0.8rem">ASSET</div>
        <div style="font-size:1.1rem;font-weight:700;color:#8b5cf6">{intent.get('asset') or 'N/A'}</div></div>""",
        unsafe_allow_html=True)
    with icols[2]:
        st.markdown(f"""<div class="metric-box"><div style="color:#64748b;font-size:0.8rem">AMOUNT</div>
        <div style="font-size:1.1rem;font-weight:700;color:#ec4899">${intent.get('amount') or 0:,.0f}</div></div>""",
        unsafe_allow_html=True)
    with icols[3]:
        total_a = sum(1 for r in results if r["verdict"] == "ALLOW")
        total_b = sum(1 for r in results if r["verdict"] == "BLOCK")
        st.markdown(f"""<div class="metric-box"><div style="color:#64748b;font-size:0.8rem">VERDICTS</div>
        <div style="font-size:1.1rem;font-weight:700"><span style="color:#22c55e">✅ {total_a}</span>
        &nbsp;<span style="color:#ef4444">🚫 {total_b}</span></div></div>""",
        unsafe_allow_html=True)

    st.divider()

    # Intent Graph
    st.markdown("### Intent Graph (Allowed Action Space)")
    fig = draw_intent_graph(G, results)
    st.pyplot(fig, use_container_width=True)

    st.divider()

    # Enforcement Results
    st.markdown("### Enforcement Pipeline Results")
    for r in results:
        render_enforcement_result(r)

    st.divider()

    # Risk breakdown for last result
    last_risk = next(
        (r["checks"][2].get("detail") for r in reversed(results) if len(r["checks"]) > 2),
        None
    )
    if last_risk and "factors" in last_risk:
        st.markdown("### Risk Factor Breakdown (Last Action)")
        factors = last_risk["factors"]
        weights = last_risk["weights"]
        df = pd.DataFrame([
            {
                "Factor": k.replace("_", " ").title(),
                "Raw Score": v,
                "Weight": weights.get(k, 0),
                "Weighted": round(v * weights.get(k, 0), 4)
            }
            for k, v in factors.items()
        ])
        df = df.sort_values("Weighted", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Audit Log
    st.divider()
    st.markdown("### Audit Log (Full Session)")
    all_logs = st.session_state.enforcement_log
    if all_logs:
        for log in reversed(all_logs[-20:]):
            verdict = log["verdict"]
            icon = "✅" if verdict == "ALLOW" else "🚫"
            color = "#22c55e" if verdict == "ALLOW" else "#ef4444"
            ts = log["timestamp"].split("T")[1][:8]
            st.markdown(f"""
            <div class="log-entry">
                <span style="color:{color}">{icon} {verdict}</span>
                &nbsp;|&nbsp; <span style="color:#94a3b8">{log['current_step']} → {log['next_step']}</span>
                &nbsp;|&nbsp; <span style="color:#64748b">{log['action'].get('type','')} {log['action'].get('asset','')}</span>
                &nbsp;|&nbsp; <span style="color:#475569">{ts}</span>
                &nbsp;|&nbsp; <span style="color:#3b82f6">Risk: {log.get('risk_score',0):.3f}</span>
                {f'<br><span style="color:#ef4444;font-size:0.75rem">Blocked: {log["block_reason"]}</span>' if verdict == "BLOCK" else ""}
            </div>
            """, unsafe_allow_html=True)

        if st.button("Export Logs as JSON"):
            logs_json = json.dumps(all_logs, indent=2)
            st.download_button(
                "Download logs.json",
                data=logs_json,
                file_name=f"armorclaw_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

elif not user_input:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color:#475569;">
        <div style="font-size:3rem;"></div>
        <div style="font-size:1.2rem; margin-top:12px; font-family:'JetBrains Mono',monospace;">ArmorClaw is standing guard</div>
        <div style="font-size:0.9rem; margin-top:8px;">Enter an agent instruction above or pick a quick scenario from the sidebar</div>
    </div>
    """, unsafe_allow_html=True)