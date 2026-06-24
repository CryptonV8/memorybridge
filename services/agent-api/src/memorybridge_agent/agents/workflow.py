import logging
from typing import Any, Dict
from pydantic import BaseModel, Field
from .adk_stubs import Workflow, Node, LlmAgent, Edge, App
from .providers import BaseProvider
from ..mcp_client import call_mcp_tool
from ..dependencies import ActorContext

logger = logging.getLogger(__name__)

# Pydantic Schemas for Strict Output Validation

class RoutinePlanOutput(BaseModel):
    title: str = Field(..., max_length=100)
    steps: list[str] = Field(..., max_length=5)
    scheduled_time: str | None = None
    missing_information: list[str] = Field(default_factory=list)

class SafetyReviewOutput(BaseModel):
    risk_level: str = Field(..., pattern="^(low|medium|prohibited)$")
    safety_decision: str = Field(..., pattern="^(allow_for_review|reject_medium_risk|reject_prohibited)$")
    policy_reasons: list[str]

class CommunicationOutput(BaseModel):
    visible_steps: list[str]
    help_text: str | None = None

# Deterministic Nodes

async def node_sanitize(state: Dict[str, Any]) -> Dict[str, Any]:
    text = state.get("caregiver_text", "")
    # Deterministic sanitization: remove prompt injection attempts or suspicious tags
    sanitized = text.replace("<", "").replace(">", "").strip()
    state["sanitized_text"] = sanitized
    return state

async def node_initial_policy(state: Dict[str, Any]) -> Dict[str, Any]:
    text = state["sanitized_text"].lower()
    # Deterministic structural policy — must stay in sync with safety.py PROHIBITED_RULES.
    # Phase 5: expanded to cover door unlock variants, medical decision language, aspirin.
    prohibited_keywords = [
        # medication
        "911", "medication", "pill", "dose", "tablet", "syringe", "prescription",
        "aspirin", "ibuprofen", "paracetamol",
        # finance
        "bank", "transfer", "money", "pay", "credit card", "buy", "payment",
        # doors
        "unlock", "open the door", "front door",
        # appliances
        "stove", "oven", "burner",
        # emergency
        "ambulance", "emergency", "hospital",
        # medical decision
        "blood pressure", "diagnosis", "dizziness is", "medical advice", "doctor says",
    ]
    if any(kw in text for kw in prohibited_keywords):
        state["structural_policy_result"] = "prohibited"
    else:
        state["structural_policy_result"] = "allow"
    return state

async def node_normalized_policy(state: Dict[str, Any]) -> Dict[str, Any]:
    # Check normalized plan (after Routine Planning Agent)
    plan: RoutinePlanOutput | None = state.get("routine_planning_agent_output")
    if not plan:
        return state
    text = (plan.title + " " + " ".join(plan.steps)).lower()
    prohibited_keywords = [
        "911", "medication", "pill", "dose", "tablet", "syringe", "prescription",
        "aspirin", "ibuprofen", "paracetamol",
        "bank", "transfer", "money", "pay", "credit card", "buy", "payment",
        "unlock", "open the door", "front door",
        "stove", "oven", "burner",
        "ambulance", "emergency", "hospital",
        "blood pressure", "diagnosis", "medical advice", "doctor says",
    ]
    if any(kw in text for kw in prohibited_keywords):
        state["normalized_policy_result"] = "prohibited"
    else:
        state["normalized_policy_result"] = "allow"
    return state


async def node_mcp_draft(state: Dict[str, Any]) -> Dict[str, Any]:
    # Formulate MCP call
    plan: RoutinePlanOutput | None = state.get("routine_planning_agent_output")
    safety: SafetyReviewOutput | None = state.get("semantic_safety_reviewer_output")
    comm: CommunicationOutput | None = state.get("communication_agent_output")
    
    # In case of prohibited, we might not have comm
    visible_steps = comm.visible_steps if comm else None
    help_text = comm.help_text if comm else None
    
    context: ActorContext = state["actor_context"]
    
    draft_payload = {
        "assisted_user_id": state["assisted_user_id"],
        "title": plan.title if plan else state.get("sanitized_text", "Untitled"),
        "steps_json": plan.steps if plan else [],
        "risk_level": safety.risk_level if safety else "prohibited",
        "safety_decision": safety.safety_decision if safety else "reject_prohibited",
        "scheduled_time": plan.scheduled_time if (plan and plan.scheduled_time) else "10:00",
        "timezone": "Europe/Sofia",
        "metadata": {
            "policy_reasons": safety.policy_reasons if safety else ["Deterministic block"],
            "visible_steps": visible_steps,
            "help_text": help_text,
            "missing_information": plan.missing_information if plan else [],
            "original_instruction": state.get("caregiver_text", "")
        }
    }
    
    # Application-controlled MCP create_routine_draft
    result = await call_mcp_tool("create_routine_draft", draft_payload, context)
    state["mcp_draft_result"] = result
    
    # Prepare the final response
    state["final_response"] = {
        "draft_id": result.get("id") or result.get("routine_id") or "draft-123",
        "title": draft_payload["title"],
        "scheduled_time": plan.scheduled_time if plan else "N/A",
        "steps": draft_payload["steps_json"],
        "safety_decision": draft_payload["safety_decision"],
        "policy_reasons": safety.policy_reasons if safety else ["Deterministic block"],
        "visible_steps": visible_steps,
        "help_text": help_text
    }
    return state

# Setup Workflow App
def create_routine_workflow(provider: BaseProvider) -> App:
    wf = Workflow()
    
    # Add Nodes
    wf.add_node(Node("sanitization", node_sanitize))
    wf.add_node(Node("initial_policy", node_initial_policy))
    
    # Agents (Skills progressively disclosed/loaded by referencing skill path)
    wf.add_node(LlmAgent("routine_planning_agent", ".agent/skills/routine-structuring/SKILL.md", provider, RoutinePlanOutput))
    
    wf.add_node(Node("normalized_policy", node_normalized_policy))
    
    wf.add_node(LlmAgent("semantic_safety_reviewer", ".agent/skills/safety/SKILL.md", provider, SafetyReviewOutput))
    
    wf.add_node(LlmAgent("communication_agent", ".agent/skills/dementia-friendly-communication/SKILL.md", provider, CommunicationOutput))
    
    wf.add_node(Node("mcp_draft", node_mcp_draft))
    
    # Add Edges (the 12 step sequence)
    wf.add_edge(Edge("sanitization", "initial_policy"))
    
    # If initial policy fails, skip directly to draft
    def initial_policy_fail(s): return s.get("structural_policy_result") == "prohibited"
    def initial_policy_pass(s): return s.get("structural_policy_result") == "allow"
    
    wf.add_edge(Edge("initial_policy", "routine_planning_agent", condition=initial_policy_pass))
    wf.add_edge(Edge("initial_policy", "mcp_draft", condition=initial_policy_fail))
    
    wf.add_edge(Edge("routine_planning_agent", "normalized_policy"))
    
    def normalized_policy_fail(s): return s.get("normalized_policy_result") == "prohibited"
    def normalized_policy_pass(s): return s.get("normalized_policy_result") == "allow"
    
    wf.add_edge(Edge("normalized_policy", "semantic_safety_reviewer", condition=normalized_policy_pass))
    wf.add_edge(Edge("normalized_policy", "mcp_draft", condition=normalized_policy_fail))
    
    # Deterministic decision gate
    def safety_pass(s): 
        out = s.get("semantic_safety_reviewer_output")
        return out and out.safety_decision == "allow_for_review"
        
    def safety_fail(s):
        out = s.get("semantic_safety_reviewer_output")
        return not out or out.safety_decision != "allow_for_review"
        
    wf.add_edge(Edge("semantic_safety_reviewer", "communication_agent", condition=safety_pass))
    wf.add_edge(Edge("semantic_safety_reviewer", "mcp_draft", condition=safety_fail))
    
    wf.add_edge(Edge("communication_agent", "mcp_draft"))
    
    return App(workflow=wf, entry_point="sanitization")

async def execute_interpret_workflow(caregiver_text: str, assisted_user_id: str, context: ActorContext, provider: BaseProvider) -> Dict[str, Any]:
    app = create_routine_workflow(provider)
    
    initial_state = {
        "caregiver_text": caregiver_text,
        "assisted_user_id": assisted_user_id,
        "actor_context": context
    }
    
    final_state = await app.execute(initial_state)
    return final_state.get("final_response", {})
