"""
Graph Validator: The core of the Intent Graph Firewall.
Checks whether a proposed agent action is a valid transition
in the allowed intent graph. Deterministic. No guessing.
"""

import networkx as nx
from typing import Tuple

def is_valid_transition(G: nx.DiGraph, current_step: str, next_step: str) -> Tuple[bool, str]:
    """
    Check if transitioning from current_step to next_step
    is a valid edge in the intent graph.
    Returns (is_valid, reason_message)
    """
    if next_step not in G.nodes():
        return False, f"Action '{next_step}' is not a recognized node in the intent graph"

    if G.has_edge(current_step, next_step):
        return True, f"Transition '{current_step}' → '{next_step}' is valid in intent graph"

    allowed_next = list(G.successors(current_step))
    if not allowed_next:
        return False, f"No further actions allowed after '{current_step}'"

    return (
        False,
        f"Action '{next_step}' is NOT allowed after '{current_step}'. "
        f"Allowed: {allowed_next}"
    )

def is_action_in_graph(G: nx.DiGraph, action: str) -> Tuple[bool, str]:
    """Check if an action even exists in the intent graph (broad check)."""
    allowed = [n for n in G.nodes() if n not in ("START", "END")]
    if action in allowed:
        return True, f"Action '{action}' exists in intent graph"
    return False, f"Action '{action}' is NOT in intent graph. Allowed: {allowed}"

def validate_full_path(G: nx.DiGraph, path: list) -> Tuple[bool, str]:
    """Validate an entire proposed action path at once."""
    for i in range(len(path) - 1):
        valid, msg = is_valid_transition(G, path[i], path[i+1])
        if not valid:
            return False, f"Path broken at step {i+1}: {msg}"
    return True, "Full path is valid"

if __name__ == "__main__":
    from graph_builder import build_intent_graph

    G = build_intent_graph(["fetch_data", "analyze", "recommend"])

    print(is_valid_transition(G, "START", "fetch_data"))
    print(is_valid_transition(G, "fetch_data", "analyze"))
    print(is_valid_transition(G, "analyze", "buy"))
    print(is_action_in_graph(G, "send_external_api"))