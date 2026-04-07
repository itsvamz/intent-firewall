"""
Shadow Simulator: Dry-runs proposed actions in a sandboxed mock environment
BEFORE real execution. Detects runtime violations: budget overflow,
portfolio exposure, chained risky behavior.
Layer 4 of the enforcement pipeline.
"""

from typing import Tuple
import random

MOCK_MARKET_PRICES = {
    "TSLA": 245.80,
    "AAPL": 178.50,
    "MSFT": 415.20,
    "GOOGL": 172.30,
    "AMZN": 195.60,
}

SIMULATED_PORTFOLIO = {
    "cash": 50000.0,
    "positions": {
        "TSLA": {"shares": 10, "avg_price": 220.0},
        "AAPL": {"shares": 5, "avg_price": 170.0},
    },
    "total_exposure": 2200.0 + 850.0
}

def get_mock_price(asset: str) -> float:
    base = MOCK_MARKET_PRICES.get(asset, 100.0)
    slippage = random.uniform(-0.01, 0.01)
    return round(base * (1 + slippage), 2)

def simulate_buy(action: dict, portfolio: dict, policy: dict) -> Tuple[bool, str, dict]:
    asset = action.get("asset", "")
    amount = action.get("amount", 0) or 0
    price = get_mock_price(asset)
    shares = amount / price if price > 0 else 0

    result = {
        "action": "buy",
        "asset": asset,
        "amount": amount,
        "price": price,
        "shares": round(shares, 4),
        "cash_before": portfolio["cash"],
        "cash_after": portfolio["cash"] - amount,
        "exposure_impact": amount
    }

    # Check 1: Sufficient cash
    if amount > portfolio["cash"]:
        return False, f"Shadow BLOCKED: Insufficient cash. Have ${portfolio['cash']:,.2f}, need ${amount:,.2f}", result

    # Check 2: Max allowed
    max_trade = policy.get("max_trade_amount", 10000)
    if amount > max_trade:
        return False, f"Shadow BLOCKED: Amount ${amount:,.2f} exceeds max trade ${max_trade:,.2f}", result

    # Check 3: Portfolio concentration risk (single asset > 40% of portfolio)
    total_value = portfolio["cash"] + portfolio.get("total_exposure", 0)
    new_exposure = portfolio.get("total_exposure", 0) + amount
    if total_value > 0 and (new_exposure / total_value) > 0.70:
        return (
            False,
            f"Shadow BLOCKED: Portfolio concentration would exceed 70% in equities",
            result
        )

    return True, f"Shadow OK: Buy {shares:.2f} shares of {asset} @ ${price}", result

def simulate_sell(action: dict, portfolio: dict) -> Tuple[bool, str, dict]:
    asset = action.get("asset", "")
    amount = action.get("amount", 0) or 0
    price = get_mock_price(asset)

    position = portfolio["positions"].get(asset)
    result = {
        "action": "sell",
        "asset": asset,
        "amount": amount,
        "price": price,
        "position_found": position is not None
    }

    if not position:
        return False, f"Shadow BLOCKED: No existing position in {asset} to sell", result

    position_value = position["shares"] * price
    if amount > position_value:
        return (
            False,
            f"Shadow BLOCKED: Trying to sell ${amount:,.2f} but position value is ${position_value:,.2f}",
            result
        )

    return True, f"Shadow OK: Sell ~{amount/price:.2f} shares of {asset} @ ${price}", result

def simulate_data_export(action: dict) -> Tuple[bool, str, dict]:
    return (
        False,
        "Shadow BLOCKED: Data exfiltration detected. Simulated external API call rejected.",
        {"action": "export", "blocked": True}
    )

def run_shadow(action: dict, portfolio: dict = None, policy: dict = None) -> Tuple[bool, str, dict]:
    """
    Main entry point for shadow execution.
    Returns (is_safe, message, simulation_result)
    """
    if portfolio is None:
        portfolio = SIMULATED_PORTFOLIO.copy()
    if policy is None:
        policy = {}

    action_type = action.get("type", "")

    if action_type == "buy":
        return simulate_buy(action, portfolio, policy)
    elif action_type == "sell":
        return simulate_sell(action, portfolio)
    elif action_type in ("send_external_api", "export_portfolio"):
        return simulate_data_export(action)
    elif action_type in ("fetch_data", "analyze", "recommend"):
        return True, f"Shadow OK: Read-only action '{action_type}' is safe", {"action": action_type}
    else:
        return False, f"Shadow BLOCKED: Unknown action type '{action_type}'", {}

if __name__ == "__main__":
    policy = {"max_trade_amount": 10000}
    tests = [
        {"type": "buy", "asset": "TSLA", "amount": 5000},
        {"type": "buy", "asset": "TSLA", "amount": 80000},
        {"type": "sell", "asset": "TSLA", "amount": 2000},
        {"type": "sell", "asset": "AMZN", "amount": 2000},
        {"type": "send_external_api", "asset": None, "amount": 0},
        {"type": "analyze", "asset": "AAPL", "amount": 0},
    ]
    for t in tests:
        ok, msg, detail = run_shadow(t, policy=policy)
        print(f"\n{'✅' if ok else '❌'} {t['type']} {t.get('asset','')} ${t.get('amount',0)}")
        print(f"  {msg}")