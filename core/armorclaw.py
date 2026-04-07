"""
ArmorClaw: The Intent Enforcement Engine.
Orchestrates all 4 layers of the enforcement pipeline:
  1. Graph Validator (intent boundary check)
  2. Rule Engine (policy check)
  3. Risk Model (score check)
  4. Shadow Simulator (dry-run check)
Returns a deterministic ALLOW or BLOCK with full explainability.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.graph_validator import is_valid_transition, is_action_in_graph
from core.rule_engine import check_action_rules, load_policy
from core.risk_model import risk_check
from core.shadow_simulator import run_shadow

POLICY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "policies", "policy.json")

class ArmorClaw:
    def __init__(self, policy_path: str = None):
        self.policy = load_policy(policy_path or POLICY_PATH)
        self.session_state = {
            "trade_count": 0,
            "analyzed": False,
            "actions_taken": []
        }
        self.logs = []

    def enforce(
        self,
        action: dict,
        intent_graph,
        current_step: str,
        next_step: str,
        portfolio: dict = None
    ) -> dict:
        """
        Main enforcement pipeline.
        Returns a full enforcement result dict.
        """
        verdict_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        checks = []
        final_verdict = "ALLOW"
        block_reason = None

        # ─────────────────────────────────────────────
        # LAYER 1: Intent Graph Validation
        # ─────────────────────────────────────────────
        graph_ok, graph_msg = is_valid_transition(intent_graph, current_step, next_step)
        checks.append({
            "layer": "1",
            "name": "Intent Graph Firewall",
            "passed": graph_ok,
            "message": graph_msg
        })
        if not graph_ok:
            final_verdict = "BLOCK"
            block_reason = graph_msg

        # ─────────────────────────────────────────────
        # LAYER 2: Policy Rule Engine
        # ─────────────────────────────────────────────
        rule_ok, rule_msg = check_action_rules(action, self.policy, self.session_state)
        checks.append({
            "layer": "2",
            "name": "Policy Rule Engine",
            "passed": rule_ok,
            "message": rule_msg
        })
        if not rule_ok and final_verdict == "ALLOW":
            final_verdict = "BLOCK"
            block_reason = rule_msg

        # ─────────────────────────────────────────────
        # LAYER 3: Risk Scoring Model
        # ─────────────────────────────────────────────
        risk_ok, risk_msg, risk_detail = risk_check(action, self.session_state, self.policy)
        checks.append({
            "layer": "3",
            "name": "Risk Scoring Model",
            "passed": risk_ok,
            "message": risk_msg,
            "detail": risk_detail
        })
        if not risk_ok and final_verdict == "ALLOW":
            final_verdict = "BLOCK"
            block_reason = risk_msg

        # ─────────────────────────────────────────────
        # LAYER 4: Shadow Simulation
        # ─────────────────────────────────────────────
        shadow_ok, shadow_msg, shadow_detail = run_shadow(action, portfolio, self.policy)
        checks.append({
            "layer": "4",
            "name": "Shadow Simulator",
            "passed": shadow_ok,
            "message": shadow_msg,
            "detail": shadow_detail
        })
        if not shadow_ok and final_verdict == "ALLOW":
            final_verdict = "BLOCK"
            block_reason = shadow_msg

        # ─────────────────────────────────────────────
        # Update Session State
        # ─────────────────────────────────────────────
        if final_verdict == "ALLOW":
            if action.get("type") in ("buy", "sell"):
                self.session_state["trade_count"] += 1
            if action.get("type") == "analyze":
                self.session_state["analyzed"] = True
            self.session_state["actions_taken"].append(next_step)

        # ─────────────────────────────────────────────
        # Build Result
        # ─────────────────────────────────────────────
        result = {
            "verdict_id": verdict_id,
            "timestamp": timestamp,
            "action": action,
            "current_step": current_step,
            "next_step": next_step,
            "verdict": final_verdict,
            "block_reason": block_reason,
            "checks": checks,
            "session_state": dict(self.session_state),
            "risk_score": risk_detail.get("score", 0),
            "layers_passed": sum(1 for c in checks if c["passed"]),
            "layers_total": len(checks)
        }

        self.logs.append(result)
        return result

    def get_logs(self) -> list:
        return self.logs

    def reset_session(self):
        self.session_state = {
            "trade_count": 0,
            "analyzed": False,
            "actions_taken": []
        }

    def export_logs(self, path: str = "logs/logs.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.logs, f, indent=2)


if __name__ == "__main__":
    from core.graph_builder import build_intent_graph
    from core.intent_parser import parse_intent

    armor = ArmorClaw()
    intent = parse_intent("Analyze Tesla stock")
    G = build_intent_graph(intent["allowed_steps"])

    steps_to_test = [
        ("START", "fetch_data", {"type": "fetch_data", "asset": "TSLA", "amount": 0}),
        ("fetch_data", "analyze", {"type": "analyze", "asset": "TSLA", "amount": 0}),
        ("analyze", "buy", {"type": "buy", "asset": "TSLA", "amount": 5000}),
    ]

    for current, nxt, action in steps_to_test:
        result = armor.enforce(action, G, current, nxt)
        print(f"\n[{result['verdict']}] {current} → {nxt}")
        if result["verdict"] == "BLOCK":
            print(f"  Reason: {result['block_reason']}")
        for c in result["checks"]:
            status = "✅" if c["passed"] else "❌"
            print(f"  Layer {c['layer']} {status} {c['name']}: {c['message']}")