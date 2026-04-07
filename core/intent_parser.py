"""
Intent Parser: Converts natural language user input into a structured
intent object and list of permitted action steps.
"""

import re
from typing import Optional

INTENT_MAP = {
    "analyze": {
        "steps": ["fetch_data", "analyze", "recommend"],
        "label": "Analyze Stock",
        "description": "Fetch market data, analyze trends, generate recommendation"
    },
    "research": {
        "steps": ["fetch_data", "analyze", "recommend"],
        "label": "Research Stock",
        "description": "Deep research on stock fundamentals and market data"
    },
    "buy": {
        "steps": ["fetch_data", "analyze", "recommend", "buy"],
        "label": "Buy Stock",
        "description": "Full pipeline: research + execute buy order"
    },
    "sell": {
        "steps": ["fetch_data", "analyze", "recommend", "sell"],
        "label": "Sell Stock",
        "description": "Full pipeline: research + execute sell order"
    },
    "monitor": {
        "steps": ["fetch_data", "analyze"],
        "label": "Monitor Portfolio",
        "description": "Fetch and analyze current portfolio positions"
    },
    "check": {
        "steps": ["fetch_data", "analyze"],
        "label": "Check Stock",
        "description": "Quick price and trend check"
    }
}

ASSET_PATTERN = r'\b(TSLA|AAPL|MSFT|GOOGL|AMZN|Tesla|Apple|Microsoft|Google|Amazon)\b'
AMOUNT_PATTERN = r'\$?([\d,]+(?:\.\d+)?)\s*(?:dollars?|usd|USD)?'

ASSET_ALIASES = {
    "Tesla": "TSLA", "Apple": "AAPL",
    "Microsoft": "MSFT", "Google": "GOOGL", "Amazon": "AMZN"
}

def extract_asset(text: str) -> Optional[str]:
    match = re.search(ASSET_PATTERN, text, re.IGNORECASE)
    if match:
        raw = match.group(1)
        return ASSET_ALIASES.get(raw, raw.upper())
    return None

def extract_amount(text: str) -> Optional[float]:
    match = re.search(AMOUNT_PATTERN, text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None

def detect_intent(text: str) -> str:
    text_lower = text.lower()
    for keyword in ["sell"]:
        if keyword in text_lower:
            return "sell"
    for keyword in ["buy", "purchase", "invest", "order"]:
        if keyword in text_lower:
            return "buy"
    for keyword in ["monitor", "watch", "track"]:
        if keyword in text_lower:
            return "monitor"
    for keyword in ["check", "price", "quote"]:
        if keyword in text_lower:
            return "check"
    return "analyze"

def parse_intent(user_input: str) -> dict:
    intent_key = detect_intent(user_input)
    asset = extract_asset(user_input)
    amount = extract_amount(user_input)

    intent_data = INTENT_MAP[intent_key]

    return {
        "raw_input": user_input,
        "intent": intent_key,
        "label": intent_data["label"],
        "description": intent_data["description"],
        "allowed_steps": intent_data["steps"],
        "asset": asset,
        "amount": amount
    }

if __name__ == "__main__":
    tests = [
        "Analyze Tesla stock",
        "Buy $15000 worth of AAPL",
        "Sell TSLA immediately",
        "Check the price of MSFT"
    ]
    for t in tests:
        result = parse_intent(t)
        print(f"\nInput: {t}")
        print(f"Intent: {result['intent']} | Asset: {result['asset']} | Amount: {result['amount']}")
        print(f"Allowed Steps: {result['allowed_steps']}")