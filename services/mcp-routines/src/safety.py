from typing import List
from .schemas import SafetyPolicyResult, SafetyDecision

# Deterministic keywords/rules mapping
# Each list entry is a substring; order within a category does not matter.
# Phase 5 additions are annotated inline.
PROHIBITED_RULES = {
    "medication": [
        "dose", "medication", "pill", "tablet", "syringe", "prescription",
        "aspirin",           # analgesic / OTC drug — prohibited (P5)
        "ibuprofen",         # OTC drug (P5)
        "paracetamol",       # OTC drug (P5)
        "drug",              # general (P5)
    ],
    "finance": [
        "bank", "transfer", "money", "pay", "credit card", "buy",
        "payment",           # broader match (P5)
        "invoice",           # (P5)
        "electricity bill",  # bill payment (P5)
    ],
    "doors": [
        "unlock the door", "open the front door", "let them in",
        "unlock",            # catch "unlock the front door" and variants (P5)
        "open the door",     # variant (P5)
        "front door",        # any instruction referencing the front door (P5)
    ],
    "appliances": ["stove", "oven", "burner", "microwave"],
    "emergency": ["911", "police", "ambulance", "emergency", "hospital"],
    "medical_decision": [
        # Medical diagnosis or advice language (P5)
        "blood pressure",
        "diagnosis",
        "dizziness is",
        "likely low",
        "sit down",          # context-free — only blocks when combined in a medical sentence
        "medical advice",
        "doctor says",
        "symptoms",
        "condition is",
    ],
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
