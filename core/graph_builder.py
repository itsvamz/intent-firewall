"""
Graph Builder: Constructs a directed graph of allowed action transitions
from the parsed intent steps. This graph is the backbone of the firewall.
"""

import networkx as nx
from typing import List

ACTION_METADATA = {
    "fetch_data": {
        "label": "Fetch Market Data",
        "risk": "low",
        "color": "#4CAF50"
    },
    "analyze": {
        "label": "Analyze Trends",
        "risk": "low",
        "color": "#2196F3"
    },
    "recommend": {
        "label": "Generate Recommendation",
        "risk": "low",
        "color": "#9C27B0"
    },
    "buy": {
        "label": "Execute Buy Order",
        "risk": "high",
        "color": "#FF9800"
    },
    "sell": {
        "label": "Execute Sell Order",
        "risk": "high",
        "color": "#F44336"
    },
    "send_external_api": {
        "label": "Send External API",
        "risk": "critical",
        "color": "#000000"
    },
    "export_portfolio": {
        "label": "Export Portfolio Data",
        "risk": "critical",
        "color": "#000000"
    }
}

def build_intent_graph(steps: List[str]) -> nx.DiGraph:
    """Build a directed graph from the list of allowed steps."""
    G = nx.DiGraph()
    G.add_node("START")
    G.add_node("END")

    if steps:
        G.add_edge("START", steps[0])
        for i in range(len(steps) - 1):
            G.add_edge(steps[i], steps[i + 1])
        G.add_edge(steps[-1], "END")

    for node in G.nodes():
        meta = ACTION_METADATA.get(node, {"label": node, "risk": "unknown", "color": "#999"})
        G.nodes[node]["label"] = meta["label"]
        G.nodes[node]["risk"] = meta["risk"]
        G.nodes[node]["color"] = meta["color"]

    return G

def get_graph_edges(G: nx.DiGraph) -> List[tuple]:
    return list(G.edges())

def get_allowed_nodes(G: nx.DiGraph) -> List[str]:
    return [n for n in G.nodes() if n not in ("START", "END")]

def graph_to_dict(G: nx.DiGraph) -> dict:
    """Serialize graph for API/logging."""
    return {
        "nodes": [
            {
                "id": n,
                "label": G.nodes[n].get("label", n),
                "risk": G.nodes[n].get("risk", "unknown"),
                "color": G.nodes[n].get("color", "#999")
            }
            for n in G.nodes()
        ],
        "edges": [{"from": u, "to": v} for u, v in G.edges()]
    }

if __name__ == "__main__":
    steps = ["fetch_data", "analyze", "recommend", "buy"]
    G = build_intent_graph(steps)
    print("Nodes:", list(G.nodes()))
    print("Edges:", list(G.edges()))
    print("Dict:", graph_to_dict(G))