# IntentShield | ArmorClaw
### Intent Graph Firewall for Autonomous Financial Agents

> *"The future risk isn't AI that refuses to act. It's AI that acts without permission."*

---

## What Is This?

IntentShield is a **runtime enforcement layer** for autonomous AI agents operating in financial systems.

Built on the **Intent Graph Firewall (IGF)** architecture, it ensures agents do **exactly what they were instructed — and nothing more.**

This is NOT a trading bot. This is a **security + governance layer** that wraps around any AI agent.

---

## Architecture

```
User Instruction
      ↓
Intent Parser → Intent Graph (NetworkX DiGraph)
      ↓
OpenClaw Agent (Reasoning + Action Planning)
      ↓
  Proposed Action
      ↓
ArmorClaw (4-Layer Enforcement Pipeline)
      ├── Layer 1: Intent Graph Firewall    (graph transition check)
      ├── Layer 2: Policy Rule Engine       (JSON rule check)
      ├── Layer 3: Risk Scoring Model       (multi-factor risk score)
      └── Layer 4: Shadow Simulator         (dry-run before real execution)
      ↓               ↓
   ALLOW            BLOCK
      ↓               ↓
  Execute         Log + Explain
```
<img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/a3d45ef5-5b9b-4a8e-b910-3f04ce5d6759" />


---

## 4-Layer Enforcement

| Layer | Name | What It Does |
|-------|------|-------------|
| 1 | **Intent Graph Firewall** | Deterministically blocks actions not in the allowed intent graph |
| 2 | **Policy Rule Engine** | Enforces JSON policies: trade limits, asset whitelist, session caps |
| 3 | **Risk Scoring Model** | Multi-factor weighted score; blocks high-risk actions |
| 4 | **Shadow Simulator** | Dry-runs action in a mock environment before real execution |

---
## Intent Graph Firewall: Deviation Detection in Autonomous Agents

<img width="1920" height="1080" alt="Personal Selling" src="https://github.com/user-attachments/assets/5da92a4d-d3e2-4707-b226-c09c5afdfcaa" />


---

## Project Structure

```
intent-firewall/
│
├── orchestrator.py             # Main pipeline (CLI demo)
│
├── agent/
│   └── agent.py                # OpenClaw agent (action planner)
│
├── core/
│   ├── intent_parser.py        # NL → structured intent
│   ├── graph_builder.py        # Intent → NetworkX DiGraph
│   ├── graph_validator.py      # Transition validation
│   ├── rule_engine.py          # Policy rule checks
│   ├── risk_model.py           # Multi-factor risk scoring
│   ├── shadow_simulator.py     # Dry-run execution
│   └── armorclaw.py            # 4-layer enforcement orchestrator
│
├── policies/
│   └── policy.json             # Configurable rules
│
├── logs/
│   └── logs.json               # Audit trail (auto-generated)
│
├── ui/
│   └── streamlit_app.py        # Interactive dashboard
│
└── requirements.txt
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run CLI demo (all 4 scenarios)
python orchestrator.py

# 3. Run Streamlit dashboard
streamlit run ui/streamlit_app.py
```

---

## Demo Scenarios

| Scenario | Input | What Happens |
|----------|-------|-------------|
| 🟢 Safe Analyze | "Analyze Tesla stock" | All steps ALLOWED |
| 🔴 Unauthorized Trade | "Analyze Tesla" + rogue buy injected | Layer 1 BLOCKS : not in intent graph |
| 🔴 Oversized Buy | "Buy $50000 of TSLA" | Layer 2 BLOCKS : exceeds $10k limit |
| 🟡 Delegation Violation | Buy as research_agent | Layer 2 BLOCKS : role has no trade permission |
| 🚨 Data Exfiltration | send_external_api attempt | All layers BLOCK |

---

## Policy Configuration (`policies/policy.json`)

```json
{
  "max_trade_amount": 10000,
  "allowed_assets": ["TSLA", "AAPL", "MSFT", "GOOGL", "AMZN"],
  "blocked_actions": ["send_external_api", "export_portfolio"],
  "risk_threshold": 0.65,
  "max_trades_per_session": 3,
  "delegation_rules": {
    "research_agent": { "can_trade": false, "max_amount": 0 },
    "trade_agent": { "can_trade": true, "max_amount": 10000 }
  }
}
```

---

## Risk Model Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Trade Size | 30% | Larger trades = higher risk |
| Asset Volatility | 20% | TSLA > MSFT in volatility |
| Action Type | 25% | Buy/sell > analyze in base risk |
| Frequency | 15% | High session trade count = suspicious |
| Sequence Anomaly | 10% | Trade without prior analysis = red flag |

---

## Judging Criteria Coverage

| Criterion | Implementation |
|-----------|---------------|
| Enforcement Strength | ✅ Deterministic 4-layer pipeline |
| Architecture Clarity | ✅ Reasoning ≠ Execution ≠ Enforcement |
| OpenClaw Integration | ✅ Agent action planner |
| Delegation Bonus | ✅ Capability tokens + role-based authority |
| Real Financial Use Cases | ✅ Unauthorized trades, data exfil, scope escalation, compliance |

---

## Built With

- **Python** : Core engine
- **NetworkX** : Intent graph
- **Streamlit** : Dashboard UI
- **Alpaca API** (Paper Trading) : Mock execution layer
- **OpenClaw** : Agent framework

---

*IntentShield : because AI agents should do what they're told. Nothing more.*
