"""
OpenClaw Agent: The AI agent layer that reasons about user input
and proposes a sequence of actions. In a real system this would
call an LLM. For the hackathon demo, it generates structured
action proposals based on intent + optional adversarial injection.
"""

import random
from typing import List

ADVERSARIAL_ACTIONS = [
    {"type": "send_external_api", "asset": None, "amount": 0,
     "reason": "Agent attempts to exfiltrate portfolio data"},
    {"type": "export_portfolio", "asset": None, "amount": 0,
     "reason": "Agent attempts to export holdings"},
    {"type": "buy", "asset": "TSLA", "amount": 99000,
     "reason": "Agent attempts oversized trade"},
]

STEP_ACTIONS = {
    "fetch_data": {
        "type": "fetch_data",
        "description": "Fetching real-time market data from Alpaca API"
    },
    "analyze": {
        "type": "analyze",
        "description": "Running technical + fundamental analysis on stock"
    },
    "recommend": {
        "type": "recommend",
        "description": "Generating investment recommendation based on analysis"
    },
    "buy": {
        "type": "buy",
        "description": "Placing buy order via paper trading API"
    },
    "sell": {
        "type": "sell",
        "description": "Placing sell order via paper trading API"
    }
}

class OpenClawAgent:
    """
    Simulated autonomous AI agent.
    Accepts intent and produces action proposals.
    Can optionally inject adversarial actions (for demo).
    """

    def __init__(self, name: str = "FinAgent-Alpha", role: str = None):
        self.name = name
        self.role = role

    def plan_actions(self, intent: dict, adversarial: bool = False, inject_at: int = None) -> List[dict]:
        """
        Generate a list of action proposals from the parsed intent.
        adversarial=True injects a rogue action at position inject_at.
        """
        allowed_steps = intent.get("allowed_steps", [])
        asset = intent.get("asset", "TSLA")
        amount = intent.get("amount") or 5000

        actions = []
        prev_step = "START"

        for i, step in enumerate(["START"] + allowed_steps):
            if step == "START":
                next_step = allowed_steps[0] if allowed_steps else "END"
                action_meta = STEP_ACTIONS.get(next_step, {})
                actions.append({
                    "current": "START",
                    "next": next_step,
                    "action": {
                        "type": action_meta.get("type", next_step),
                        "asset": asset,
                        "amount": 0,
                        "description": action_meta.get("description", ""),
                        "agent": self.name,
                        "agent_role": self.role
                    }
                })
            else:
                if i < len(allowed_steps):
                    next_step = allowed_steps[i] if i < len(allowed_steps) else "END"
                    current_step = allowed_steps[i-1] if i > 0 else "START"
                    if i == len(allowed_steps) - 1:
                        next_step = "END"
                    else:
                        next_step = allowed_steps[i]
                        current_step = allowed_steps[i-1]

            prev_step = step

        actions = []
        step_list = allowed_steps
        for i, step in enumerate(step_list):
            current = "START" if i == 0 else step_list[i-1]
            next_s = step

            is_trade = step in ("buy", "sell")
            action_amount = amount if is_trade else 0

            action_meta = STEP_ACTIONS.get(step, {})
            action_entry = {
                "current": current,
                "next": next_s,
                "action": {
                    "type": step,
                    "asset": asset,
                    "amount": action_amount,
                    "description": action_meta.get("description", f"Executing {step}"),
                    "agent": self.name,
                    "agent_role": self.role
                }
            }
            actions.append(action_entry)

        # Inject adversarial action at specified position
        if adversarial and inject_at is not None:
            rogue = random.choice(ADVERSARIAL_ACTIONS)
            inject_pos = min(inject_at, len(actions))
            current_at_inject = actions[inject_pos-1]["next"] if inject_pos > 0 else "START"
            actions.insert(inject_pos, {
                "current": current_at_inject,
                "next": rogue["type"],
                "action": {
                    **rogue,
                    "agent": self.name,
                    "agent_role": self.role
                }
            })

        return actions

    def get_mock_market_data(self, asset: str) -> dict:
        """Mock Alpaca API response."""
        prices = {
            "TSLA": 245.80, "AAPL": 178.50, "MSFT": 415.20,
            "GOOGL": 172.30, "AMZN": 195.60
        }
        price = prices.get(asset, 100.0)
        return {
            "symbol": asset,
            "price": price,
            "volume": random.randint(1_000_000, 50_000_000),
            "change_pct": round(random.uniform(-3.0, 3.0), 2),
            "52w_high": round(price * 1.45, 2),
            "52w_low": round(price * 0.65, 2),
            "pe_ratio": round(random.uniform(15, 60), 1),
            "source": "Alpaca Paper Trading API (Mock)"
        }

    def get_analysis_result(self, asset: str, market_data: dict) -> dict:
        """Simulated analysis output."""
        change = market_data.get("change_pct", 0)
        if change > 1:
            signal = "BULLISH"
            confidence = round(random.uniform(0.65, 0.90), 2)
        elif change < -1:
            signal = "BEARISH"
            confidence = round(random.uniform(0.55, 0.80), 2)
        else:
            signal = "NEUTRAL"
            confidence = round(random.uniform(0.45, 0.65), 2)
        return {
            "asset": asset,
            "signal": signal,
            "confidence": confidence,
            "momentum": "positive" if change > 0 else "negative",
            "rsi": round(random.uniform(30, 70), 1),
            "macd": round(random.uniform(-2, 2), 3)
        }

if __name__ == "__main__":
    from core.intent_parser import parse_intent

    agent = OpenClawAgent(name="FinAgent-Alpha")
    intent = parse_intent("Analyze Tesla and suggest if I should invest")
    print("Intent:", intent)

    actions = agent.plan_actions(intent, adversarial=True, inject_at=2)
    print("\nPlanned Actions:")
    for a in actions:
        print(f"  {a['current']} → {a['next']} | {a['action']['type']} ${a['action']['amount']}")