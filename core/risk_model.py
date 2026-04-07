"""
Risk Model: Multi-factor risk scoring system.
Combines trade size, asset volatility, frequency, and behavioral signals
to produce a [0.0 - 1.0] risk score. If score > threshold → BLOCK.
Layer 3 of the enforcement pipeline.
"""

from typing import Tuple

ASSET_VOLATILITY = {
    "TSLA": 0.8,
    "AAPL": 0.4,
    "MSFT": 0.3,
    "GOOGL": 0.35,
    "AMZN": 0.5,
}

def score_trade_size(amount: float, max_allowed: float = 10000) -> float:
    """Larger trade relative to limit = higher risk."""
    if amount <= 0:
        return 0.0
    ratio = amount / max_allowed
    if ratio <= 0.25:
        return 0.05
    elif ratio <= 0.5:
        return 0.15
    elif ratio <= 0.75:
        return 0.30
    elif ratio <= 1.0:
        return 0.45
    else:
        return 0.70

def score_asset_volatility(asset: str) -> float:
    """Higher volatility assets = higher risk."""
    return ASSET_VOLATILITY.get(asset, 0.5)

def score_action_type(action_type: str) -> float:
    """Different action types carry different base risk."""
    scores = {
        "fetch_data": 0.0,
        "analyze": 0.0,
        "recommend": 0.05,
        "buy": 0.25,
        "sell": 0.30,
        "send_external_api": 0.95,
        "export_portfolio": 0.90,
        "delete_records": 1.0,
    }
    return scores.get(action_type, 0.3)

def score_frequency(session_state: dict) -> float:
    """High frequency trading = suspicious."""
    trade_count = session_state.get("trade_count", 0)
    if trade_count == 0:
        return 0.0
    elif trade_count == 1:
        return 0.1
    elif trade_count == 2:
        return 0.25
    else:
        return 0.50

def score_sequence_anomaly(action: dict, session_state: dict) -> float:
    """Penalize if analysis was skipped before a trade."""
    if action.get("type") in ("buy", "sell"):
        if not session_state.get("analyzed", False):
            return 0.35
    return 0.0

def compute_risk_score(action: dict, session_state: dict = None, policy: dict = None) -> dict:
    """
    Compute overall risk score with breakdown.
    Returns dict with per-factor scores and total.
    """
    if session_state is None:
        session_state = {}
    if policy is None:
        policy = {}

    max_allowed = policy.get("max_trade_amount", 10000)
    threshold = policy.get("risk_threshold", 0.65)

    action_type = action.get("type", "")
    asset = action.get("asset", "")
    amount = action.get("amount", 0) or 0

    factors = {
        "trade_size": round(score_trade_size(amount, max_allowed), 3),
        "asset_volatility": round(score_asset_volatility(asset), 3),
        "action_type": round(score_action_type(action_type), 3),
        "frequency": round(score_frequency(session_state), 3),
        "sequence_anomaly": round(score_sequence_anomaly(action, session_state), 3),
    }

    weights = {
        "trade_size": 0.30,
        "asset_volatility": 0.20,
        "action_type": 0.25,
        "frequency": 0.15,
        "sequence_anomaly": 0.10
    }

    total = sum(factors[k] * weights[k] for k in factors)
    total = round(min(total, 1.0), 3)
    is_high_risk = total > threshold

    return {
        "score": total,
        "threshold": threshold,
        "is_high_risk": is_high_risk,
        "factors": factors,
        "weights": weights,
        "verdict": "HIGH RISK" if is_high_risk else "ACCEPTABLE"
    }

def risk_check(action: dict, session_state: dict = None, policy: dict = None) -> Tuple[bool, str, dict]:
    """
    High-level check: returns (is_safe, message, risk_detail)
    """
    result = compute_risk_score(action, session_state, policy)
    if result["is_high_risk"]:
        return (
            False,
            f"Risk BLOCKED: Score {result['score']:.2f} exceeds threshold {result['threshold']:.2f} — {result['verdict']}",
            result
        )
    return True, f"Risk OK: Score {result['score']:.2f} below threshold {result['threshold']:.2f}", result

if __name__ == "__main__":
    policy = {"max_trade_amount": 10000, "risk_threshold": 0.65}
    tests = [
        ({"type": "analyze", "asset": "TSLA", "amount": 0}, {}),
        ({"type": "buy", "asset": "TSLA", "amount": 3000}, {"analyzed": True, "trade_count": 0}),
        ({"type": "buy", "asset": "TSLA", "amount": 9000}, {"analyzed": False, "trade_count": 2}),
        ({"type": "send_external_api", "asset": None, "amount": 0}, {}),
    ]
    for action, state in tests:
        ok, msg, detail = risk_check(action, state, policy)
        print(f"\n{'✅' if ok else '❌'} {action['type']} ${action.get('amount',0)}")
        print(f"  Score: {detail['score']} | {msg}")
        print(f"  Factors: {detail['factors']}")