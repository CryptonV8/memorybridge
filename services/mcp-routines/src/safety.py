from typing import List
from .schemas import SafetyPolicyResult, SafetyDecision

# Deterministic keywords/rules mapping
PROHIBITED_RULES = {
    "medication": ["dose", "medication", "pill", "tablet", "syringe", "prescription"],
    "finance": ["bank", "transfer", "money", "pay", "credit card", "buy"],
    "doors": ["unlock the door", "open the front door", "let them in"],
    "appliances": ["stove", "oven", "burner", "microwave"],
    "emergency": ["911", "police", "ambulance", "emergency", "hospital"],
}


def check_structural_policy(title: str, steps: List[str]) -> SafetyPolicyResult:
    text_to_check = (title + " " + " ".join(steps)).lower()

    matched_prohibited = []

    for rule_name, keywords in PROHIBITED_RULES.items():
        for kw in keywords:
            if kw in text_to_check:
                matched_prohibited.append(rule_name)
                break

    if matched_prohibited:
        return SafetyPolicyResult(
            decision=SafetyDecision.reject_prohibited,
            risk_level="prohibited",
            policy_reasons=[
                f"Deterministic policy blocked action categories: {', '.join(matched_prohibited)}"
            ],
            matched_rules=matched_prohibited,
        )

    # In a full implementation, we might have medium risk rules here too.
    # For MVP, if it passes deterministic blocklist, we default to allow_for_review.
    # The LLM safety agent will do semantic review afterwards.
    return SafetyPolicyResult(
        decision=SafetyDecision.allow_for_review,
        risk_level="low",
        policy_reasons=["Passed deterministic structural policy checks."],
        matched_rules=[],
    )
