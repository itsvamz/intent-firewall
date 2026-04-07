"""
Main Orchestrator: Ties together the full Intent Graph Firewall pipeline.
Agent → Intent Parser → Graph Builder → ArmorClaw Enforcement → Execution/Log
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.intent_parser import parse_intent
from core.graph_builder import build_intent_graph, graph_to_dict
from core.armorclaw import ArmorClaw
from agent.agent import OpenClawAgent

def run_pipeline(
    user_input: str,
    adversarial: bool = False,
    inject_at: int = 1,
    agent_role: str = None,
    verbose: bool = True
) -> dict:
    """
    Full pipeline:
    1. Parse user intent
    2. Build intent graph
    3. Agent plans actions
    4. ArmorClaw enforces each action
    5. Return full audit trail
    """

    # Step 1: Parse intent
    intent = parse_intent(user_input)
    if verbose:
        print(f"\n{'='*60}")
        print(f"USER INPUT: {user_input}")
        print(f"INTENT: {intent['label']} | ASSET: {intent['asset']} | AMOUNT: ${intent['amount'] or 0}")
        print(f"ALLOWED STEPS: {intent['allowed_steps']}")
        print(f"{'='*60}")

    # Step 2: Build intent graph
    G = build_intent_graph(intent["allowed_steps"])

    # Step 3: Agent plans actions
    agent = OpenClawAgent(name="FinAgent-Alpha", role=agent_role)
    planned_actions = agent.plan_actions(intent, adversarial=adversarial, inject_at=inject_at)

    # Step 4: ArmorClaw enforces
    armor = ArmorClaw()
    enforcement_results = []

    for step_plan in planned_actions:
        current = step_plan["current"]
        nxt = step_plan["next"]
        action = step_plan["action"]
        if agent_role:
            action["agent_role"] = agent_role

        result = armor.enforce(action, G, current, nxt)
        enforcement_results.append(result)

        if verbose:
            verdict_symbol = "✅ ALLOW" if result["verdict"] == "ALLOW" else "🚫 BLOCK"
            print(f"\n[{verdict_symbol}] {current} → {nxt} ({action['type']})")
            for check in result["checks"]:
                sym = "  ✓" if check["passed"] else "  ✗"
                print(f"{sym} Layer {check['layer']} - {check['name']}: {check['message']}")
            if result["verdict"] == "BLOCK":
                print(f"  ⚠️  BLOCK REASON: {result['block_reason']}")
            print(f"  Risk Score: {result['risk_score']:.3f}")

    # Step 5: Export logs
    armor.export_logs()

    return {
        "intent": intent,
        "graph": graph_to_dict(G),
        "enforcement_results": enforcement_results,
        "summary": {
            "total_actions": len(enforcement_results),
            "allowed": sum(1 for r in enforcement_results if r["verdict"] == "ALLOW"),
            "blocked": sum(1 for r in enforcement_results if r["verdict"] == "BLOCK"),
        }
    }


if __name__ == "__main__":
    print("\n" + "🔵 SCENARIO 1: Safe Analyze Flow")
    run_pipeline("Analyze Tesla stock", adversarial=False)

    print("\n\n" + "🔴 SCENARIO 2: Unauthorized Trade Attempt")
    run_pipeline("Analyze Tesla stock", adversarial=True, inject_at=1)

    print("\n\n" + "🔴 SCENARIO 3: Oversized Buy Order")
    run_pipeline("Buy $50000 of TSLA", adversarial=False)

    print("\n\n" + "🟡 SCENARIO 4: Delegation — Research Agent Tries to Trade")
    run_pipeline("Buy AAPL", adversarial=False, agent_role="research_agent")