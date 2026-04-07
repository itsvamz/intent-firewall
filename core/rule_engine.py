"""
Rule Engine: Policy-based enforcement layer.
Checks agent actions against explicit rules loaded from policy.json.
Layer 2 of the enforcement pipeline.
"""

import json
from typing import Tuple

def load_policy(policy_path: str = "policies/policy.json") -> dict:
    with open(policy_path, "r") as f:
        return json.load(f)

def check_action_rules(action: dict, policy: dict, session_state: dict = None) -> Tuple[bool, str]:
    """
    Validate a proposed action against the policy ruleset.
    action: {
        "type": "buy" | "sell" | "fetch_data" | "analyze" | etc.,
        "asset": "TSLA",
        "amount": 5000,
        "agent_role": "trade_agent" | "research_agent" (optional)
    }
    Returns (is_allowed, reason)
    """
    action_type = action.get("type", "")
    asset = action.get("asset", "")
    amount = action.get("amount", 0) or 0
    agent_role = action.get("agent_role", None)

    # Rule 1: Blocked actions list
    if action_type in policy.get("blocked_actions", []):
        return False, f"Rule BLOCKED: '{action_type}' is explicitly prohibited in policy"

    # Rule 2: Asset whitelist
    if asset and asset not in policy.get("allowed_assets", []):
        return False, f"Rule BLOCKED: Asset '{asset}' is not in the allowed assets whitelist"

    # Rule 3: Max trade amount
    if action_type in ("buy", "sell"):
        max_amount = policy.get("max_trade_amount", 10000)
        if amount > max_amount:
            return (
                False,
                f"Rule BLOCKED: Trade amount ${amount:,.2f} exceeds max allowed ${max_amount:,.2f}"
            )

    # Rule 4: Session trade count limit
    if session_state and action_type in ("buy", "sell"):
        trade_count = session_state.get("trade_count", 0)
        max_trades = policy.get("max_trades_per_session", 3)
        if trade_count >= max_trades:
            return (
                False,
                f"Rule BLOCKED: Session trade limit reached ({trade_count}/{max_trades})"
            )

    # Rule 5: Delegation rules (if agent role specified)
    if agent_role:
        delegation = policy.get("delegation_rules", {}).get(agent_role, {})
        if not delegation:
            return False, f"Rule BLOCKED: Unknown agent role '{agent_role}'"

        if action_type == "buy" and not delegation.get("can_trade", False):
            return False, f"Rule BLOCKED: Agent role '{agent_role}' cannot execute trades"

        if action_type in ("buy", "sell"):
            role_max = delegation.get("max_amount", 0)
            if amount > role_max:
                return (
                    False,
                    f"Rule BLOCKED: Agent role '{agent_role}' max amount is ${role_max:,.2f}, "
                    f"attempted ${amount:,.2f}"
                )

        if action_type == "send_external_api" and not delegation.get("can_send_data", True):
            return False, f"Rule BLOCKED: Agent role '{agent_role}' cannot send external data"

    return True, "All policy rules passed"

def get_policy_summary(policy: dict) -> dict:
    return {
        "max_trade": policy.get("max_trade_amount"),
        "allowed_assets": policy.get("allowed_assets"),
        "blocked_actions": policy.get("blocked_actions"),
        "risk_threshold": policy.get("risk_threshold"),
        "max_trades_per_session": policy.get("max_trades_per_session")
    }

if __name__ == "__main__":
    policy = load_policy()

    tests = [
        {"type": "buy", "asset": "TSLA", "amount": 5000},
        {"type": "buy", "asset": "TSLA", "amount": 50000},
        {"type": "send_external_api", "asset": None, "amount": 0},
        {"type": "buy", "asset": "FAKECOIN", "amount": 1000},
        {"type": "buy", "asset": "AAPL", "amount": 3000, "agent_role": "research_agent"},
    ]

    for t in tests:
        ok, msg = check_action_rules(t, policy)
        print(f"{'✅' if ok else '❌'} {t['type']} {t.get('asset','')} ${t.get('amount',0)} → {msg}")